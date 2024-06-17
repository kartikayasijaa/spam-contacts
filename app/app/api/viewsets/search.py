from rest_framework.response import Response
from app.models.user import User
from app.models.contact import Contact
from django.db.models import Q, Value
from app.serializers import output
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

def get_query_type(query):
    if query[0].isdigit():
        return 'phone_number'
    return 'name'

class SearchView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JWTAuthentication,)
    output_serializer_class = output.SearchOutputSerializer

    def get(self, request):
        query = request.query_params.get('q', None)
        results = []

        if not query:
            return Response({'error': 'Search query is required.'}, status=400)

        search_type = get_query_type(query)
        
        if search_type == 'phone_number':
            user_exact_matches = User.objects.filter(phone_number=query)

            if user_exact_matches.exists():
                results = user_exact_matches
            
            else:
                contact_exact_matches = Contact.objects.filter(phone_number=query)
                if contact_exact_matches.exists():
                    results = contact_exact_matches

        else:
            user_starts_with = User.objects.filter(
                Q(first_name__istartswith=query) | Q(last_name__istartswith=query)
            )
            user_contains = User.objects.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query)
            ).exclude(
                Q(first_name__istartswith=query) | Q(last_name__istartswith=query)
            )


            contact_starts_with = Contact.objects.filter(
                Q(first_name__istartswith=query) | Q(last_name__istartswith=query)
            )
            contact_contains = Contact.objects.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query)
            ).exclude(
                Q(first_name__istartswith=query) | Q(last_name__istartswith=query)
            )

            results = list(user_starts_with) + list(contact_starts_with) + list(user_contains) + list(contact_contains)

            
        output_serializer = self.output_serializer_class(results, many=True)

        return Response(output_serializer.data)

        

class SearchDetailsView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JWTAuthentication,)
    output_user_serializer_class = output.SearchDetailsUserOutputSerializer
    output_contact_serializer_class = output.ContactOutputSerializer

    def get(self, request, id):
        user = User.objects.filter(id=id).first()
        if user:
            is_contact_of_user = user.created_contacts.filter(created_by=request.user).exists()
            if is_contact_of_user:
                user.email = None

            output_serializer = self.output_user_serializer_class(user)
            return Response(output_serializer.data)
        else:
            contact = Contact.objects.filter(id=id).first()        
            output_serializer = self.output_contact_serializer_class(contact)
            return Response(output_serializer.data)