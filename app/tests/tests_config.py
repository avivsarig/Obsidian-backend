TEST_PROFILES = {
    "unit": {
        "description": "Minimal setup for unit tests",
        "requires_vault": False,
        "requires_git": False,
        "requires_auth": False,
        "mock_level": "high",
    },
    "integration": {
        "description": "Real components for integration tests",
        "requires_vault": True,
        "requires_git": False,
        "requires_auth": True,
        "mock_level": "medium",
    },
    "e2e": {
        "description": "End-to-end testing with full stack",
        "requires_vault": True,
        "requires_git": True,
        "requires_auth": True,
        "mock_level": "low",
    },
}

REQUIRED_ENDPOINTS = {
    "health": {"/health"},
    "tasks": {
        "/tasks/",
        "/tasks/{task_id}",
        "/tasks/process-active",
        "/tasks/process-completed",
    },
    "vault": {"/vault/pull"},
}

REQUIRED_HTTP_METHODS = {"health": {"GET"}, "tasks": {"GET", "POST"}, "vault": {"POST"}}

REQUIRED_TAGS = {"health", "tasks", "vault"}

PERFORMANCE_THRESHOLDS = {
    "router_analysis": {"max_time_ms": 100},
    "vault_operations": {"max_time_ms": 500},
    "file_operations": {"max_time_ms": 200},
    "api_requests": {"max_time_ms": 1000},
}

TEST_TASK_TEMPLATE = {
    "title": "Test Task",
    "content": "Test task content",
    "is_project": False,
    "done": False,
    "is_high_priority": False,
    "do_date": "2025-06-18",
    "due_date": "",
    "completed_at": "",
    "repeat_task": "",
}

TEST_ARCHIVE_TEMPLATE = {
    "title": "Test Archive",
    "content": "Archived content",
    "tags": ["test"],
    "created_at": "2025-06-18T14:30:00",
    "URL": "",
}

VAULT_SEED_TEMPLATES = {
    "minimal": {
        "Tasks": {
            "Simple Task": {
                "frontmatter": {"done": False, "is_project": False},
                "content": "A simple test task",
            }
        }
    },
    "realistic": {
        "Tasks": {
            "Daily Review": {
                "frontmatter": {
                    "done": False,
                    "is_project": False,
                    "do_date": "2025-06-18",
                    "repeat_task": "0 9 * * *",
                },
                "content": "Review yesterday's work and plan today",
            },
            "Project Planning": {
                "frontmatter": {
                    "done": False,
                    "is_project": True,
                    "due_date": "2025-06-25",
                },
                "content": "Plan the next project milestone",
            },
        },
        "Tasks/Completed": {
            "Finished Task": {
                "frontmatter": {"done": True, "completed_at": "2025-06-17T16:30:00"},
                "content": "A task that was completed",
            }
        },
    },
}


class TestStandards:
    @staticmethod
    def get_profile_config(profile_name: str) -> dict:
        return TEST_PROFILES.get(profile_name, TEST_PROFILES["unit"])

    @staticmethod
    def validate_api_coverage(router_analysis: dict) -> dict[str, bool]:
        results = {}

        actual_paths = set(router_analysis.get("route_paths", []))
        for category, required in REQUIRED_ENDPOINTS.items():
            covered = any(
                any(
                    req_path.replace("{task_id}", "test") in path
                    for path in actual_paths
                )
                for req_path in required
            )
            results[f"{category}_endpoints"] = covered

        actual_methods = router_analysis.get("route_methods", set())
        for category, required in REQUIRED_HTTP_METHODS.items():
            covered = required.issubset(actual_methods)
            results[f"{category}_methods"] = covered

        return results

    @staticmethod
    def check_performance_threshold(
        metric_name: str, value: float, unit: str = "ms"
    ) -> bool:
        threshold_config = PERFORMANCE_THRESHOLDS.get(metric_name)
        if not threshold_config:
            return True

        if unit == "ms":
            max_allowed = threshold_config.get("max_time_ms", float("inf"))
            return value <= max_allowed

        return True

    @staticmethod
    def get_seed_data(template_name: str = "minimal") -> dict:
        return VAULT_SEED_TEMPLATES.get(template_name, VAULT_SEED_TEMPLATES["minimal"])
