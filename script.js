let images = ["Kashmir.jpeg", "ShimlaManali.jpeg"];
let pdfs = ["web_itinerary/Kashmir.pdf", "web_itinerary/ShimlaManali.pdf"];
let currentIndex = 0;
let imgElement = document.getElementById("sliderImage");

function nextImage() {
    imgElement.classList.add("fade-out");
    setTimeout(() => {
        currentIndex = (currentIndex + 1) % images.length;
        imgElement.src = images[currentIndex];
        imgElement.classList.remove("fade-out");
    }, 500);
}

function prevImage() {
    imgElement.classList.add("fade-out");
    setTimeout(() => {
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        imgElement.src = images[currentIndex];
        imgElement.classList.remove("fade-out");
    }, 500);
}

function downloadPDF() {
    const link = document.createElement("a");
    link.href = pdfs[currentIndex]; // Download corresponding PDF for the current image
    link.download = pdfs[currentIndex];
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

setInterval(nextImage, 3000); // Auto slide every 3 seconds
