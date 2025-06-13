from django.contrib import admin
from .models import Product,ProductCategory,OrderProductOnline,SearchProduct,Subproduct,Region

admin.site.register([Product,ProductCategory,OrderProductOnline,SearchProduct,Subproduct,Region])