import uuid as uuid_pkg

from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies import authorize_user
from src.gov_structures.models import GovStructure, GovStructureCreate
from src.service import create_model, receive_model, receive_models

gov_structures_router = APIRouter(
    prefix='/government-structures',
    tags=['government-structures']
)


@gov_structures_router.post('/', dependencies=[Depends(authorize_user(is_government_worker=True))])
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
    """View that processes getting all government structures"""

    gov_structure = await receive_model(GovStructure, GovStructure.uuid == uuid)  # type: ignore
    if gov_structure is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return gov_structure
