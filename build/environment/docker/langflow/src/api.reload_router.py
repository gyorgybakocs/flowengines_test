"""
This module defines a FastAPI route for dynamically reloading all Langflow components.

It provides a "hard reload" endpoint that is useful during development to see
changes in custom components without needing to restart the entire application server.
"""
import langflow.interface.components as components
from fastapi import APIRouter, HTTPException, status
from langflow.api.schemas import ReloadStatusResponse
from langflow.logging import logger
from langflow.services.deps import get_settings_service


reload_router = APIRouter(prefix="/reload", tags=["Reload"])

@reload_router.post(
    "/",
    response_model=ReloadStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Dynamically reload components"
)
async def reload_components():
    """
    Performs a hard reload of all components.

    This is achieved by completely re-instantiating the central component cache.
    The subsequent call to the component loading function will find the cache empty
    and be forced to re-read all component files from the disk, reflecting any
    changes made.
    """
    logger.info("LANGFLOW RELOAD - Received request to reload components.")
    try:
        logger.debug("Re-instantiating the global 'component_cache' object to perform a hard reset.")
        components.component_cache = components.ComponentCache()

        logger.debug("Re-populating the component types cache from scratch.")
        await components.get_and_cache_all_types_dict(get_settings_service())

        logger.info("Component refresh completed successfully.")
        return ReloadStatusResponse(
            status="success",
            message="Components refreshed successfully."
        )
    except Exception as e:
        logger.exception("Error during component refresh.")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh components: {str(e)}"
        )
