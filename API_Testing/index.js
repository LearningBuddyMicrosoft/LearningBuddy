console.log("Server starting...");
const app = require('express')();
const PORT = 8080;

app.listen(
    PORT,
    () => console.log(`Active and working on https://localhost:${PORT}`)
)
//We can send a GET request for the /tshirt Resource

//GET endpoint
app.get('/tshirt', (request, response)=>{
    response.status(200).send({
        tshirt:'Balenciaga',
        size:'small'
    })
});

//POST endpoint
app.post('/tshirt/:id', (request, response) =>{
    const { id } = request.params;
    const { logo } = request.body;

    if(!logo){
        response.status(418).send({message:'We need a logo!'})
    }
    response.send({
        tshirt:`This is your ${logo} and your ID of ${id}`
    });
});