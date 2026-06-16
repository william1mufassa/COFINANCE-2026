from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add extra user info to the JSON response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role', 'phone', 'region', 'date_of_birth', 'id_number')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cette adresse email existe déjà.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'CLIENT'),
            phone=validated_data.get('phone', ''),
            region=validated_data.get('region', ''),
            date_of_birth=validated_data.get('date_of_birth', None),
            id_number=validated_data.get('id_number', ''),
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'phone', 'region', 'date_of_birth', 'id_number', 'is_verified', 'date_joined')
        read_only_fields = ('id', 'role', 'is_verified', 'date_joined')
