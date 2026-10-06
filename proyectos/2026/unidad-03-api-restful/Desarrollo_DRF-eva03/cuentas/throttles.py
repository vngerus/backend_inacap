from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    scope = "auth"  # 5/min por IP, definido en settings.DEFAULT_THROTTLE_RATES
