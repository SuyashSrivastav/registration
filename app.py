from flask import Flask, request, jsonify
import jwt
import uuid
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SECRET_KEY"] = "your-secret-key"
client = MongoClient("mongodb://localhost:27018/")
db = client["mydatabase"]

# Check if users collection exists, if not create one
if "users" not in db.list_collection_names():
    users_collection = db.create_collection("users")
else:
    users_collection = db["users"]


# Endpoint for OTP-based login/signup
@app.route("/api/auth/otp", methods=["POST"])
def login():
    email = request.json.get("email")
    if not email:
        return jsonify({"message": "Email address is required"}), 400

    # Check if user already exists
    user = users_collection.find_one({"email": email})
    if user:
        user_id = str(user["_id"])
        first_name = user["first_name"]
        last_name = user["last_name"]
        city = user["city"]
        state = user["state"]
        country = user["country"]
        photo_url = user["photo_url"]
    else:
        # Create new user if not found
        user_id = str(uuid.uuid4())
        first_name = ""
        last_name = ""
        city = ""
        state = ""
        country = ""
        photo_url = None
        user = {
            "_id": user_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "city": city,
            "state": state,
            "country": country,
            "photo_url": photo_url,
        }
        users_collection.insert_one(user)

    # Generate JWT token for authentication
    token = jwt.encode(
        {"user_id": user_id}, app.config["SECRET_KEY"], algorithm="HS256"
    )

    # Return success response with token and user details
    return jsonify(
        {
            "message": "Success",
            "token": token,
            "user_id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "city": city,
            "state": state,
            "country": country,
            "photo_url": photo_url,
        }
    )


# Endpoint for profile view
@app.route("/api/users/<string:user_id>/profile", methods=["GET"])
def get_profile(user_id):
    try:
        user = users_collection.find_one({"_id": user_id})
        if user:
            first_name = user["first_name"]
            last_name = user["last_name"]
            city = user["city"]
            state = user["state"]
            country = user["country"]
            photo_url = user["photo_url"]
            return jsonify(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "city": city,
                    "state": state,
                    "country": country,
                    "photo_url": photo_url,
                }
            )
        else:
            return jsonify({"message": "User not found"}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# Endpoint for updating user profile
@app.route("/api/users/<user_id>/profile", methods=["PUT"])
def update_profile(user_id):
    # Check if user exists
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Get request parameters
    first_name = request.json.get("first_name")
    last_name = request.json.get("last_name")
    city = request.json.get("city")
    state = request.json.get("state")
    country = request.json.get("country")

    # Validate request parameters
    if not first_name:
        return jsonify({"message": "First name is required"}), 400
    if not last_name:
        return jsonify({"message": "Last name is required"}), 400
    if not city:
        return jsonify({"message": "City is required"}), 400
    if not state:
        return jsonify({"message": "State is required"}), 400
    if not country:
        return jsonify({"message": "Country is required"}), 400

    # Update user profile in database
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "first_name": first_name,
                "last_name": last_name,
                "city": city,
                "state": state,
                "country": country,
            }
        },
    )

    # Return success response
    return jsonify({"message": "Success"})


# Endpoint for photo upload
@app.route("/api/users/<user_id>/photo", methods=["POST"])
def upload_photo(user_id):
    # Check if user exists
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Check if photo file is uploaded
    if "photo" not in request.files:
        return jsonify({"message": "Photo is required"}), 400

    # Save uploaded photo
    photo_file = request.files["photo"]
    if photo_file.filename == "":
        return jsonify({"message": "Photo file is empty"}), 400
    if not allowed_file(photo_file.filename):
        return jsonify({"message": "Invalid file type"}), 400

    filename = secure_filename(photo_file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    photo_file.save(save_path)

    # Update user's photo URL in database
    photo_url = f"http://localhost:5000/{save_path}"
    users.update_one({"_id": ObjectId(user_id)}, {"$set": {"photo_url": photo_url}})

    return jsonify({"message": "Success", "photo_url": photo_url}), 200


# Helper function to check if file type is allowed
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        "png",
        "jpg",
        "jpeg",
        "gif",
    }


if __name__ == "__main__":
    app.run(debug=True)
