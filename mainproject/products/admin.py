from django.contrib import admin
from .models import Product,ProductCategory,OrderProductOnline,SearchProduct,Subproduct,Category,Region

admin.site.register([Category,Product,ProductCategory,OrderProductOnline,SearchProduct,Subproduct,Region])