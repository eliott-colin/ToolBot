//récup données
    data = await fetch(`https://replit.com/@eliottcolinpro/ImaginativeValidFormulas#{1315724850521706566:%20'1315724850521706566'}_messages.json`)
    .then(response => response.json())
    .catch(error => alert("Erreur : " + error));

    console.log(data);
