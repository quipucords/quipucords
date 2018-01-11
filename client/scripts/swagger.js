const express = require('express');
const app = express();
const swaggerUi = require('swagger-ui-express');
const YAML = require('yamljs');
const swaggerDocument = YAML.load(`${process.cwd()}/../docs/swagger.yml`);
const port = process.env.PORT || 4040;

app.use('/docs/api', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

app.listen(port, function() {
  console.log(`
You can now view API docs in the browser.

  Open: http://localhost:${port}/docs/api
`);
});
