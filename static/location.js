navigator.geolocation.getCurrentPosition((position) => {
  let lat = position.coords.latitude;
  let long = position.coords.longitude;
  let url = document.getElementById("location").href;
  
  url = url + "/" + lat;
  url = url + "/" + long;
  
  document.getElementById("location").href = url;
})
