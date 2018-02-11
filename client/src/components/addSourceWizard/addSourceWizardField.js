import PropTypes from 'prop-types';
import React from 'react';
import { Form, Grid } from 'patternfly-react';

const addSourceWizardField = ({ children, colLabel = 3, colField = 9, id, label, error, errorMessage, ...props }) => {
  const setId = id || `generatedid-${Math.ceil(1e5 * Math.random())}`;

  return (
    <Form.FormGroup controlId={setId} validationState={error ? 'error' : null} {...props}>
      <Grid.Col componentClass={Form.ControlLabel} sm={colLabel}>
        {label}
      </Grid.Col>
      <Grid.Col sm={colField}>
        {children}
        {error && <Form.HelpBlock>{errorMessage}</Form.HelpBlock>}
      </Grid.Col>
    </Form.FormGroup>
  );
};

addSourceWizardField.propTypes = {
  children: PropTypes.node.isRequired,
  colLabel: PropTypes.number,
  colField: PropTypes.number,
  id: PropTypes.string,
  label: PropTypes.node,
  error: PropTypes.string,
  errorMessage: PropTypes.string
};

export { addSourceWizardField };

export default addSourceWizardField;
