from django.core.management.base import BaseCommand
from products.models import Category


class Command(BaseCommand):
    help = 'Seed category data into the database'

    def handle(self, *args, **options):
        categories_data = [
            {"name": "Cement", "slug": "cement", "icon": "🏗️"},
            {"name": "Steel & Iron", "slug": "steel", "icon": "🔩"},
            {"name": "Roofing Materials", "slug": "roofing", "icon": "🏠"},
            {"name": "Paint & Finishes", "slug": "paint", "icon": "🎨"},
            {"name": "Tiles & Flooring", "slug": "tiles", "icon": "🔲"},
            {"name": "Electrical & Plumbing", "slug": "electrical", "icon": "⚡"},
            {"name": "Doors & Windows", "slug": "doors", "icon": "🚪"},
            {"name": "Insulation", "slug": "insulation", "icon": "🧱"},
            {"name": "Hardware & Tools", "slug": "hardware", "icon": "🔧"},
            {"name": "Concrete & Aggregates", "slug": "concrete", "icon": "🪨"},
            {"name": "Timber & Wood", "slug": "timber", "icon": "🌳"},
            {"name": "Others", "slug": "others", "icon": "📦"},
        ]

        created_count = 0
        updated_count = 0

        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=category_data['slug'],
                defaults={
                    'name': category_data['name'],
                    'icon': category_data['icon'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                # Update existing category with new icon if it doesn't have one
                if not category.icon and category_data['icon']:
                    category.icon = category_data['icon']
                    category.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated category: {category.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Category already exists: {category.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding completed! Created: {created_count}, Updated: {updated_count}'
            )
        )
