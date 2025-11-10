import firebase_admin
from firebase_admin import credentials, firestore

try:
    # Initialize Firebase
    cred = credentials.Certificate("serviceaccountKey.json")
    firebase_admin.initialize_app(cred)
    print("Firebase initialized successfully!")

    # Connect to Firestore
    db = firestore.client()
    test_doc_ref = db.collection('test_collection').document('test_document')
    test_doc_ref.set({'status': 'Firebase is configured successfully!'})
    print("Firestore is working!")

    # Retrieve the document to confirm
    doc = test_doc_ref.get()
    if doc.exists:
        print("Document retrieved! Data:", doc.to_dict())
    else:
        print("Failed to retrieve the document.")

except Exception as e:
    print("Firebase configuration failed:", e)
