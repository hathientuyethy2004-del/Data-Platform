"""
Platform-level components and orchestration
"""

__all__ = ["PlatformOrchestrator", "APIGateway", "gateway_app", "api_app"]


def __getattr__(name):
	if name == "PlatformOrchestrator":
		from .orchestrator import PlatformOrchestrator

		return PlatformOrchestrator
	if name == "APIGateway":
		from .api_gateway import APIGateway

		return APIGateway
	if name == "gateway_app":
		from .api_gateway import app

		return app
	if name == "api_app":
		from .api.main import app

		return app
	raise AttributeError(name)
