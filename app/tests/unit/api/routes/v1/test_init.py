import pytest


class TestV1RouterConfiguration:
    def test_router_import_structure(self) -> None:
        try:
            from app.src.api.routes.v1 import v1_router
            from app.src.api.routes.v1.health import router as health_router
            from app.src.api.routes.v1.tasks import router as tasks_router
            from app.src.api.routes.v1.vault import router as vault_router

            routers = {
                "v1_router": v1_router,
                "health_router": health_router,
                "tasks_router": tasks_router,
                "vault_router": vault_router,
            }

            for name, router in routers.items():
                assert router is not None, f"{name} should be importable"

        except ImportError as e:
            pytest.fail(f"Required router imports not available: {e}")

    def test_router_basic_structure(self) -> None:
        from app.src.api.routes.v1 import v1_router

        assert hasattr(v1_router, "routes"), "Router should have routes"
        assert hasattr(v1_router, "prefix"), "Router should have prefix"
        assert (
            v1_router.prefix == "/v1"
        ), f"Expected prefix '/v1', got '{v1_router.prefix}'"


class TestRouterIntegration:
    def test_health_endpoint_exists(self, api_client) -> None:
        response = api_client.get("/api/v1/health")

        assert response.status_code != 404, "Health endpoint should exist"

    def test_tasks_endpoint_exists(self, api_client) -> None:
        response = api_client.get("/api/v1/tasks/")

        assert response.status_code != 404, "Tasks endpoint should exist"


if __name__ == "__main__":
    test_instance = TestV1RouterConfiguration()
    test_instance.test_router_import_structure()
    print("✅ Router import structure test passed")

    test_instance.test_router_basic_structure()
    print("✅ Router structure test passed")

    print("\n🎉 All router tests passed!")
