import os

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if line.strip() == "# Initialize MinIO Client":
        # Skip down to "SWAGGER_URL"
        pass
    if line.strip() == "# Auth Endpoints":
        break
    new_lines.append(line)

# Wait, the minio logic is:
# 59: # Initialize MinIO Client
# 65: )
# We can just use hardcoded indices:
# Keep 1 to 58
# skip 59 to 66
# keep 67 to 78
# skip 79 to 105
# keep 106 to 780
final_lines = lines[:58] + lines[66:78] + lines[105:780]

final_lines.extend([
    "\n",
    "# Register Blueprints\n",
    "from api.auth_routes import auth_bp\n",
    "from api.admin_routes import admin_bp\n",
    "from api.deck_routes import deck_bp\n",
    "from api.stats_routes import stats_bp\n",
    "from api.main_routes import main_bp\n",
    "\n",
    "app.register_blueprint(auth_bp)\n",
    "app.register_blueprint(admin_bp)\n",
    "app.register_blueprint(deck_bp)\n",
    "app.register_blueprint(stats_bp)\n",
    "app.register_blueprint(main_bp)\n",
    "\n",
    "if __name__ == '__main__':\n",
    "    app.run(debug=True, port=5000)\n"
])

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(final_lines)

print("Rewrite Complete")
