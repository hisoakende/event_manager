import uuid as uuid_pkg

from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies import authorize_user
from src.gov_structures.models import GovStructure, GovStructureCreate, GovStructureUpdate
from src.service import create_model, receive_model, receive_models, delete_models, update_models

gov_structures_router = APIRouter(
    prefix='/government-structures',
    tags=['government-structures']
)


@gov_structures_router.post('/', status_code=status.HTTP_201_CREATED,
                            dependencies=[Depends(authorize_user(is_government_worker=True))])
async def create_gov_structure(gov_structure_to_data: GovStructureCreate) -> GovStructure:
    """The view that processes creation the government structure"""

    gov_structure = GovStructure.from_orm(gov_structure_to_data)
    await create_model(gov_structure)
    return gov_structure


@gov_structures_router.get('/', dependencies=[Depends(authorize_user())])
async def receive_gov_structures() -> list[GovStructure]:
    """The view that processes getting the government structure"""

    return await receive_models(GovStructure)


@gov_structures_router.get('/{uuid}/', dependencies=[Depends(authorize_user())])
async def receive_gov_structure(uuid: uuid_pkg.UUID) -> GovStructure:
    """The view that processes getting all government structures"""

    gov_structure = await receive_model(GovStructure, GovStructure.uuid == uuid)  # type: ignore
    if gov_structure is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return gov_structure


@gov_structures_router.patch('/{uuid}/', dependencies=[Depends(authorize_user(is_government_worker=True))])
async def update_gov_structure(uuid: uuid_pkg.UUID, gov_structure_changes: GovStructureUpdate) -> GovStructure:
    """The view that processes updating the government structure"""

    is_updated = await update_models(GovStructure, gov_structure_changes)
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
