# users/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Customer, Staff

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name", "phone", "is_active", "date_joined")
        read_only_fields = ("id", "is_active", "date_joined")


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("email", "name", "phone", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return attrs

    def create(self, validated_data, is_active=True):
        # remove password2 as it's not needed for user creation
        password = validated_data.pop("password")
        validated_data.pop("password2")

        # create user with hashed password
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Staff
        fields = ("id", "user", "role", "created_at")


class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ("id", "user", "status", "created_at")


# users/serializers.py
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})


class UserLogoutSerializer(serializers.Serializer):
    pass
