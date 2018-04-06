const express = require('express');
const swaggerUi = require('swagger-ui-express');
const swaggerParser = require('swagger-parser');
const YAML = require('yamljs');
const yamlFile = `${process.cwd()}/../docs/swagger.yml`;
const app = express();
const port = process.env.PORT || 5050;
const swaggerDocument = YAML.load(yamlFile);

app.use('/docs/api', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

app.listen(port, function() {
  console.log(`\nYou can now view API docs in the browser.\n  Open: http://localhost:${port}/docs/api\n`);

  swaggerParser.validate(yamlFile, err => {
    if (err) {
      console.error(`  \x1b[31m${err.name}\n  \x1b[31m${err.message}\x1b[0m\n`);
    }
  });
});
