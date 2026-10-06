from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegistroSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), lookup="iexact", message="Ya existe una cuenta con este email.")]
    )
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")  # sin is_staff/is_superuser: nadie se auto-promueve

    def validate_password(self, value):
        password_validation.validate_password(value)  # usa AUTH_PASSWORD_VALIDATORS
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        error = serializers.ValidationError({"refresh": "Token inválido o expirado."})
        try:
            self.token = RefreshToken(attrs["refresh"])
        except TokenError:
            raise error
        if str(self.token["user_id"]) != str(self.context["request"].user.pk):
            raise error  # no se puede invalidar el token de otra persona
        return attrs

    def save(self):
        self.token.blacklist()


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_staff", "is_superuser", "is_active")
        read_only_fields = ("id", "username", "email", "is_superuser")  # admin solo cambia is_staff e is_active
