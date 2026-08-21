from flask import render_template, redirect, request, Blueprint, Response
from .service_client import ServiceClient

frontend_bp = Blueprint(
    "frontend", __name__, template_folder="templates"
)


@frontend_bp.route("/static/uploads/<path:filename>")
def product_image(filename):
    """Proxy product images from the Catalog service.

    When the Catalog service uses local storage it returns relative image URLs
    (``/static/uploads/<file>``), which the browser resolves against this
    service. Streaming them from Catalog keeps the frontend the single public
    entry point. With S3 storage the URLs are absolute and this never fires.
    """
    upstream = ServiceClient.stream("catalog", f"/static/uploads/{filename}")
    return Response(
        upstream.iter_content(chunk_size=8192),
        content_type=upstream.headers.get("Content-Type", "application/octet-stream"),
        headers={"Cache-Control": "public, max-age=3600"},
    )


@frontend_bp.route("/")
def index():
    products = ServiceClient.get("catalog", "/api/products")
    return render_template("index.html", products=products)


@frontend_bp.route("/products/<int:product_id>")
def product_detail(product_id):
    product = ServiceClient.get("catalog", f"/api/products/{product_id}")
    inventory = ServiceClient.get("inventory", f"/api/inventory/{product_id}")
    return render_template("product.html", product=product, inventory=inventory)


@frontend_bp.route("/admin")
def admin():
    products = ServiceClient.get("catalog", "/api/products")
    return render_template("admin.html", products=products)


@frontend_bp.route("/admin/add-product", methods=["POST"])
def add_product():
    form_data = {
        "name": request.form.get("name"),
        "description": request.form.get("description", ""),
        "price": request.form.get("price"),
    }

    files = {}
    if "image" in request.files and request.files["image"].filename:
        image = request.files["image"]
        files["image"] = (image.filename, image.stream, image.content_type)

    ServiceClient.post("catalog", "/api/products", data=form_data, files=files)
    return redirect("/admin")


@frontend_bp.route("/products/<int:product_id>/inventory", methods=["POST"])
def update_inventory(product_id):
    data = {
        "quantity": int(request.form.get("quantity", 0)),
        "warehouse": request.form.get("warehouse", "main"),
    }
    ServiceClient.put("inventory", f"/api/inventory/{product_id}", json=data)
    return redirect(f"/products/{product_id}")
