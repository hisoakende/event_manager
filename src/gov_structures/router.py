import uuid as uuid_pkg
from typing import Annotated

from asyncpg import UniqueViolationError, ForeignKeyViolationError
from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies import authorize_user
from src.gov_structures.models import GovStructure, GovStructureCreate, GovStructureUpdate, GovStructureSubscription
from src.gov_structures.service import receive_subs_to_gov_structure_from_db
from src.gov_structures.sfp import GovStructureSFP
from src.service import create_model, receive_model, delete_models, update_models, receive_models_by_sfp_or_filter
from src.sfp import UsersSFP
from src.users.models import UserRead

gov_structures_router = APIRouter(
    prefix='/government-structures',
    tags=['government-structures']
)


@gov_structures_router.post('/', status_code=status.HTTP_201_CREATED,
                            dependencies=[Depends(authorize_user(is_government_worker=True))])
async def create_gov_structure(gov_structure_data: GovStructureCreate) -> GovStructure:
    """The view that processes creation the government structure"""

    gov_structure = GovStructure.from_orm(gov_structure_data)
    await create_model(gov_structure)
    return gov_structure


@gov_structures_router.get('/', dependencies=[Depends(authorize_user())])
async def receive_gov_structures(
        gov_structure_sfp: Annotated[GovStructureSFP, Depends(GovStructureSFP)]) -> list[GovStructure]:
    """The view that processes getting all government structures"""

    return await receive_models_by_sfp_or_filter(GovStructure, gov_structure_sfp)


@gov_structures_router.get('/{uuid}/', dependencies=[Depends(authorize_user())])
async def receive_gov_structure(uuid: uuid_pkg.UUID) -> GovStructure:
    """The view that processes getting the government structure"""

    gov_structure = await receive_model(GovStructure, GovStructure.uuid == uuid)  # type: ignore
    if gov_structure is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return gov_structure


@gov_structures_router.patch('/{uuid}/', dependencies=[Depends(authorize_user(is_government_worker=True))])
async def update_gov_structure(uuid: uuid_pkg.UUID, gov_structure_changes: GovStructureUpdate) -> GovStructure:
    """The view that processes updating the government structure"""

    is_updated = await update_models(GovStructure, gov_structure_changes, GovStructure.uuid == uuid)  # type: ignore
    if not is_updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return await receive_model(GovStructure, GovStructure.uuid == uuid)  # type: ignore


@gov_structures_router.delete('/{uuid}/', status_code=status.HTTP_204_NO_CONTENT,
                              dependencies=[Depends(authorize_user(is_government_worker=True))])
async def delete_gov_structure(uuid: uuid_pkg.UUID) -> None:
    """The view that processes deleting the government structure"""

    is_deleted = await delete_models(GovStructure, GovStructure.uuid == uuid)  # type: ignore
    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@gov_structures_router.post('/{uuid}/subscription/', status_code=status.HTTP_204_NO_CONTENT)
async def subscribe_to_gov_structure(uuid: uuid_pkg.UUID, user_id: Annotated[int, Depends(authorize_user())]) -> None:
    """The view that processes subscribing to the government structure"""

    subscription = GovStructureSubscription(gov_structure_uuid=uuid, user_id=user_id)

    try:
        await create_model(subscription)
    except UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['path', 'uuid'],
                                     'msg': 'you have already subscribed to this government structure',
                                     'type': 'value_error'}])
    except ForeignKeyViolationError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@gov_structures_router.delete('/{uuid}/subscription/', status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_from_gov_structure(uuid: uuid_pkg.UUID,
                                         user_id: Annotated[int, Depends(authorize_user())]) -> None:
    """The view that processes unsubscribing to the government structure"""

    is_deleted = await delete_models(GovStructureSubscription,
                                     GovStructureSubscription.gov_structure_uuid == uuid,  # type: ignore
                                     GovStructureSubscription.user_id == user_id)  # type: ignore
    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@gov_structures_router.get('/{uuid}/subscribers/', dependencies=[Depends(authorize_user(is_government_worker=True))])
async def receive_subscribers_to_gov_structure(
        uuid: uuid_pkg.UUID,
        users_sfp: Annotated[UsersSFP, Depends(UsersSFP)]) -> list[UserRead]:
    """The view that processes getting subscribers to the government structure"""

    gov_structure = await receive_model(GovStructure, GovStructure.uuid == uuid)  # type: ignore
    if gov_structure is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    users = await receive_subs_to_gov_structure_from_db(uuid, users_sfp)
    return [UserRead.from_orm(user) for user in users]
