from __future__ import annotations

from dataclasses import dataclass, field


class QuotaExceededError(RuntimeError):
    def __init__(self, quota: str, limit: int) -> None:
        self.quota, self.limit = quota, limit
        super().__init__(f"{quota} quota exceeded")


class FeatureDisabledError(RuntimeError):
    def __init__(self, feature: str) -> None:
        self.feature = feature
        super().__init__(f"{feature} is disabled")


DEFAULT_QUOTAS = {
    "watchlist_items": 50,
    "strategies": 20,
    "analyses_per_day": 100,
    "backtests_per_day": 20,
    "notifications_per_day": 100,
}

DEFAULT_FLAGS = {
    "dataset_publication": True,
    "analysis": True,
    "ai_explanation": True,
    "notification_dispatch": True,
}


@dataclass
class BetaControls:
    default_quotas: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_QUOTAS))
    default_flags: dict[str, bool] = field(default_factory=lambda: dict(DEFAULT_FLAGS))
    workspace_quotas: dict[str, dict[str, int]] = field(default_factory=dict)
    workspace_flags: dict[str, dict[str, bool]] = field(default_factory=dict)

    def quota(self, workspace_id: str, name: str) -> int:
        return self.workspace_quotas.get(workspace_id, {}).get(name, self.default_quotas[name])

    def flag(self, workspace_id: str, name: str) -> bool:
        return self.workspace_flags.get(workspace_id, {}).get(name, self.default_flags[name])

    def require_feature(self, workspace_id: str, name: str) -> None:
        if not self.flag(workspace_id, name):
            raise FeatureDisabledError(name)

    def require_quota(self, workspace_id: str, name: str, current: int) -> None:
        limit = self.quota(workspace_id, name)
        if current >= limit:
            raise QuotaExceededError(name, limit)
