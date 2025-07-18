

import firebase_admin
from firebase_admin import credentials, firestore, auth


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
def delete_all_users():
    """Remove all user documents from Firestore."""
    users_ref = db.collection("users")
    docs = users_ref.stream()

    count = 0
    for doc in docs:
        print(f"Deleting user: {doc.id}")
        doc.reference.delete()
        count += 1

    print(f"Deleted {count} user(s) from the 'users' collection.")

def delete_subcollections(doc_ref):
    """Delete all direct subcollections for a document."""
    for col in doc_ref.collections():
        # Firestore allows 500 ops per batch – chunk if you need more
        batch = db.batch()
        for subdoc in col.stream():
            batch.delete(subdoc.reference)
        batch.commit()

def delete_all_apartments():
    """Remove all apartments and their nested data."""
    apartments_ref = db.collection("apartments")
    docs = apartments_ref.stream()

    count = 0
    for doc in docs:
        print(f"Deleting apartment: {doc.id}")
        delete_subcollections(doc.reference)  # First delete subcollections
        doc.reference.delete()  # Then delete the main apartment doc
        count += 1

    print(f"Deleted {count} apartment(s) and their subcollections.")


def delete_all_auth_users():
    """Delete all Firebase authentication users."""
    page = auth.list_users()
    count = 0
    while page:
        for user in page.users:
            print(f"Deleting auth user: {user.uid}")
            auth.delete_user(user.uid)
            count += 1
        page = page.get_next_page()
    print(f"Deleted {count} authentication user(s).")


if __name__ == "__main__":
    delete_all_users()
    delete_all_auth_users()
    delete_all_apartments()