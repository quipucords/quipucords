import React from 'react';
import PropTypes from 'prop-types';
import _cloneDeep from 'lodash/cloneDeep';
import _isEqual from 'lodash/isEqual';
import helpers from '../../common/helpers';

const initialState = {
  isUpdating: false,
  isSubmitting: false,
  isValid: null,
  isValidating: false,
  submitCount: 0
};

class FormState extends React.Component {
  static checkedSetValues({ setValuesAssumeBoolIsChecked, setValues }) {
    const checked = {};

    if (setValuesAssumeBoolIsChecked) {
      Object.keys(setValues).forEach(key => {
        if (typeof setValues[key] === 'boolean') {
          checked[key] = setValues[key];
        }
      });
    }

    return checked;
  }

  static isPromise(obj) {
    return Object.prototype.toString.call(obj) === '[object Promise]';
  }

  constructor(props) {
    super(props);

    this.touched = {};
    this.checked = FormState.checkedSetValues(props);

    this.refUpdating = false;
    this.refValues =
      props.resetUsingSetValues === true || props.setValuesOnUpdate === true ? _cloneDeep(props.setValues) : null;

    this.errors = {};
    this.values = _cloneDeep(props.setValues);

    this.state = {
      ...initialState
    };
  }

  componentDidMount() {
    const { validateOnMount } = this.props;

    if (validateOnMount === true) {
      this.validateOnMount();
    }
  }

  componentDidUpdate() {
    const { refValues } = this;
    const { setValuesOnUpdate, setValues } = this.props;

    if (setValuesOnUpdate === true && !_isEqual(refValues, setValues)) {
      this.updateComponentValues();
    }
  }

  onEventCustom = custom => {
    const eventArray = (Array.isArray(custom) && custom) || (custom && [custom]);

    if (!eventArray.length) {
      return;
    }

    eventArray
      .filter(event => 'name' in event && ('value' in event || 'checked' in event))
      .forEach(event => this.onEvent({ target: { ...event }, persist: helpers.noop, type: 'custom' }));
  };

  onEvent = event => {
    const { touched, values } = this;
    const { id, name, value, checked } = event.options ? { ...event } : event.target;

    event.persist();

    const targetName = name || id || 'generated form state target, add name or id attr to field';

    this.touched = { ...touched, [targetName]: true };
    this.values = { ...values, [targetName]: value };

    if (checked !== undefined) {
      this.checked = { ...this.checked, [targetName]: checked };
    }

    this.setState(
      {
        isUpdating: true,
        isValidating: true
      },
      () =>
        this.validate(event).then(updatedErrors => {
          const setUpdateErrors = { ...((updatedErrors && updatedErrors[0]) || updatedErrors || {}) };
          const checkIsValid = !Object.keys(setUpdateErrors).length;

          this.errors = setUpdateErrors;

          this.setState({
            isUpdating: false,
            isValid: checkIsValid,
            isValidating: false
          });
        })
    );
  };

  onReset = event => {
    const { refValues, values } = this;
    const { setValuesAssumeBoolIsChecked, onReset, resetUsingSetValues } = this.props;

    event.persist();

    const isResetWithSetValues = refValues && resetUsingSetValues === true;
    const updatedValues = (isResetWithSetValues && _cloneDeep(refValues)) || {};
    const updatedChecked =
      (isResetWithSetValues && FormState.checkedSetValues(setValuesAssumeBoolIsChecked, updatedValues)) || {};

    this.values = updatedValues;
    this.checked = updatedChecked;
    this.errors = {};
    this.touched = {};

    this.setState({
      ...initialState
    });

    if (isResetWithSetValues) {
      onReset({ event, ..._cloneDeep({ values: updatedValues, prevValues: values }) });
    } else {
      // Resetting the values, potentially, will throw the controlled vs uncontrolled messaging.
      onReset({ event, values: {}, ..._cloneDeep({ prevValues: values }) });
    }
  };

  onSubmit = event => {
    const { submitCount } = this.state;

    event.persist();
    event.preventDefault();

    this.setState(
      {
        submitCount: submitCount + 1,
        isSubmitting: true,
        isUpdating: true,
        isValidating: true
      },
      () =>
        this.validate(event).then(updatedErrors => {
          const setUpdateErrors = { ...((updatedErrors && updatedErrors[0]) || updatedErrors || {}) };
          const checkIsValid = !Object.keys(setUpdateErrors).length;

          this.errors = setUpdateErrors;
          this.touched = {};

          this.setState(
            {
              isValid: checkIsValid,
              isValidating: false
            },
            () =>
              checkIsValid &&
              this.submit(event).then(() => {
                this.setState({
                  isSubmitting: false,
                  isUpdating: false
                });
              })
          );
        })
    );
  };

  submit(event = { type: 'submit' }) {
    const { checked, errors, values, touched } = this;
    const { onSubmit } = this.props;

    const checkPromise = onSubmit({
      event,
      ..._cloneDeep({ ...this.state, checked, errors, values, touched })
    });

    if (FormState.isPromise(checkPromise)) {
      return checkPromise;
    }

    return {
      then: callback => callback()
    };
  }

  validate(event = { type: 'validate' }) {
    const { checked, errors, values, touched } = this;
    const { validate } = this.props;

    const checkPromise = validate({
      event,
      ..._cloneDeep({ ...this.state, checked, errors, values, touched })
    });

    if (FormState.isPromise(checkPromise)) {
      return checkPromise;
    }

    return {
      then: callback => callback(checkPromise)
    };
  }

  validateOnMount(event = { type: 'mount' }) {
    this.validateOnUpdate(event);
  }

  validateOnUpdate(event = { type: 'update' }) {
    this.setState(
      {
        isUpdating: true,
        isValidating: true
      },
      () =>
        this.validate(event).then(updatedErrors => {
          const setUpdateErrors = { ...((updatedErrors && updatedErrors[0]) || updatedErrors || {}) };
          const checkIsValid = !Object.keys(setUpdateErrors).length;

          this.errors = setUpdateErrors;

          this.setState({
            isUpdating: false,
            isValidating: false,
            isValid: checkIsValid
          });
        })
    );
  }

  updateComponentValues() {
    const { setValues, setValuesAssumeBoolIsChecked, validateOnUpdate } = this.props;

    this.setState(
      {
        isUpdating: true
      },
      () => {
        this.checked = FormState.checkedSetValues(setValuesAssumeBoolIsChecked, setValues);
        this.refValues = _cloneDeep(setValues);
        this.values = _cloneDeep(setValues);

        if (validateOnUpdate) {
          this.validateOnUpdate();
        } else {
          this.setState({
            isUpdating: false
          });
        }
      }
    );
  }

  render() {
    const { checked, errors, values, touched } = this;
    const { children } = this.props;

    return (
      <React.Fragment>
        {children({
          handleOnEventCustom: this.onEventCustom,
          handleOnEvent: this.onEvent,
          handleOnReset: this.onReset,
          handleOnSubmit: this.onSubmit,
          ..._cloneDeep({ ...this.state, checked, errors, values, touched })
        })}
      </React.Fragment>
    );
  }
}

FormState.propTypes = {
  children: PropTypes.func.isRequired,
  onReset: PropTypes.func,
  onSubmit: PropTypes.func,
  resetUsingSetValues: PropTypes.bool,
  setValues: PropTypes.object,
  setValuesOnUpdate: PropTypes.bool,
  setValuesAssumeBoolIsChecked: PropTypes.bool,
  validate: PropTypes.func,
  validateOnMount: PropTypes.bool,
  validateOnUpdate: PropTypes.bool
};

FormState.defaultProps = {
  onReset: helpers.noop,
  onSubmit: helpers.noop,
  resetUsingSetValues: true,
  setValues: {},
  setValuesOnUpdate: false,
  setValuesAssumeBoolIsChecked: true,
  validate: helpers.noop,
  validateOnMount: false,
  validateOnUpdate: false
};

export { FormState as default, FormState };
