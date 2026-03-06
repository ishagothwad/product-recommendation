
 // Handle click on Settings link to open the modal
  document.getElementById('settingsLink').addEventListener('click', function() {
    $('#settingsModal').modal('show');
  });

  // Handle theme apply button click
  document.getElementById('applyTheme').addEventListener('click', function() {
    // Get the selected theme value
    var selectedTheme = document.querySelector('input[name="theme"]:checked').value;

    // Apply the selected theme
    if (selectedTheme === 'black') {
      document.body.style.backgroundColor = 'black';
      document.body.style.color = 'white';
    } else if (selectedTheme === 'green') {
      document.body.style.backgroundColor = 'green';
      document.body.style.color = 'white';
    } else {
      // Default theme
      document.body.style.backgroundColor = '#f8f9fa';
      document.body.style.color = 'black';
    }

    // Close the modal
    $('#settingsModal').modal('hide');
  });

  // Handle zoom in button click
  document.getElementById('zoomIn').addEventListener('click', function() {
    document.body.style.zoom = "115%";
  });

  // Handle zoom out button click
  document.getElementById('zoomOut').addEventListener('click', function() {
    document.body.style.zoom = "100%";
  });

// Handle Add to Cart button clicks

document.querySelectorAll(".add-to-cart").forEach(btn => {
    btn.addEventListener("click", () => {
        fetch("/add_to_cart", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                id: btn.dataset.id,
                name: btn.dataset.name,
                brand: btn.dataset.brand,
                price: btn.dataset.price,
                image: btn.dataset.image
            })
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById("cart-count").innerText = data.cart_count;
        });
    });
});
document.addEventListener("click", function (e) {
    if (e.target.closest(".add-to-cart")) {
        const btn = e.target.closest(".add-to-cart");

        fetch("/add_to_cart", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                id: btn.dataset.id,
                name: btn.dataset.name,
                brand: btn.dataset.brand,
                price: btn.dataset.price,
                image: btn.dataset.image
            })
        })
        .then(res => res.json())
        .then(data => {
            const count = document.getElementById("cart-count");
            if (count) count.innerText = data.cart_count;
        });
    }
});
