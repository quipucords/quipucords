import React from 'react';
import PropTypes from 'prop-types';
import { Form, Grid } from 'patternfly-react';
import helpers from '../../common/helpers';

const FormField = ({
  children,
  colLabel,
  colLabelClassName,
  colField,
  colFieldClassName,
  error,
  errorMessage,
  id,
  label,
  ...props
}) => {
  const setId = id || helpers.generateId();

  return (
    <Form.FormGroup controlId={setId} validationState={error ? 'error' : null} {...props}>
      <Grid.Col componentClass={Form.ControlLabel} className={colLabelClassName} sm={colLabel}>
        {label}
      </Grid.Col>
      <Grid.Col className={colFieldClassName} sm={colField}>
        {children}
        {error && <Form.HelpBlock>{errorMessage}</Form.HelpBlock>}
      </Grid.Col>
    </Form.FormGroup>
  );
};

const doesntHaveMinimumCharacters = (value, characters = 5) => typeof value === 'string' && value.length < characters;
const isEmpty = value => !value || value === '';

const fieldValidation = {
  doesntHaveMinimumCharacters,
  isEmpty
};

FormField.propTypes = {
  children: PropTypes.node.isRequired,
  colLabel: PropTypes.number,
  colLabelClassName: PropTypes.string,
  colField: PropTypes.number,
  colFieldClassName: PropTypes.string,
  error: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
  errorMessage: PropTypes.string,
  id: PropTypes.string,
  label: PropTypes.node
};

FormField.defaultProps = {
  colLabel: 3,
  colLabelClassName: null,
  colField: 9,
  colFieldClassName: null,
  error: null,
  errorMessage: null,
  id: null,
  label: null
};

export { FormField as default, FormField, fieldValidation };
