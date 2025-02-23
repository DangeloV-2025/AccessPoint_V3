from app import create_app, db
from app.models import Resource
from sqlalchemy import func

def remove_duplicate_resources():
    app = create_app()
    with app.app_context():
        try:
            print("Starting duplicate resource cleanup...")
            
            # Find all duplicate names
            duplicates = db.session.query(
                Resource.name,
                func.count(Resource.id).label('count')
            ).group_by(Resource.name).having(func.count(Resource.id) > 1).all()
            
            if not duplicates:
                print("No duplicates found!")
                return
            
            print(f"Found {len(duplicates)} resources with duplicates")
            total_deleted = 0
            
            for duplicate in duplicates:
                name = duplicate[0]
                count = duplicate[1]
                
                print(f"\nProcessing duplicate: {name} (found {count} copies)")
                
                # Get all resources with this name, ordered by creation date
                resources = Resource.query.filter_by(name=name)\
                    .order_by(Resource.created_at.asc())\
                    .all()
                
                # Keep the first one (oldest), delete the rest
                original = resources[0]
                duplicates_to_delete = resources[1:]
                
                print(f"Keeping resource ID: {original.id} (created: {original.created_at})")
                
                for dupe in duplicates_to_delete:
                    try:
                        print(f"Deleting duplicate ID: {dupe.id} (created: {dupe.created_at})")
                        db.session.delete(dupe)
                        total_deleted += 1
                    except Exception as e:
                        print(f"Error deleting resource {dupe.id}: {str(e)}")
                        db.session.rollback()
                        continue
                
                db.session.commit()
            
            print(f"\nCleanup completed! Deleted {total_deleted} duplicate resources.")
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    remove_duplicate_resources() 