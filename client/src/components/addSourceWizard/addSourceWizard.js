import React from 'react';
import PropTypes from 'prop-types';
import { Modal, Button, Icon, Wizard } from 'patternfly-react';
import helpers from '../../common/helpers';
import { connect } from 'react-redux';
import Store from '../../redux/store';
import CreateCredentialDialog from '../createCredentialDialog/createCredentialDialog';
import { confirmationModalTypes, sourcesTypes } from '../../redux/constants';
import { addSourceWizardSteps } from './addSourceWizardConstants';
import { addSource, updateSource } from '../../redux/actions/sourcesActions';
import AddSourceWizardStepOne from './addSourceWizardStepOne';
import AddSourceWizardStepTwo from './addSourceWizardStepTwo';
import AddSourceWizardStepThree from './addSourceWizardStepThree';

class AddSourceWizard extends React.Component {
  constructor(props) {
    super(props);

    this.initialState = {
      activeStepIndex: 0,
      show: false,
      add: false,
      edit: false,
      source: {},
      stepOneValid: false,
      stepTwoValid: false,
      fulfilled: false,
      error: false,
      errorMessage: ''
    };

    this.state = { ...this.initialState };

    helpers.bindMethods(this, ['onCancel', 'onStep', 'onNext', 'onBack', 'onSubmit']);
  }

  componentWillReceiveProps(nextProps) {
    if (!this.props.show && nextProps.show) {
      this.resetInitialState(nextProps);
    }

    if (nextProps.stepOneValid || nextProps.stepTwoValid) {
      this.setState({
        stepOneValid: nextProps.stepOneValid || false,
        stepTwoValid: nextProps.stepTwoValid || false,
        source: nextProps.source,
        fulfilled: nextProps.fulfilled,
        error: nextProps.error,
        errorMessage: nextProps.errorMessage
      });
    }
  }

  resetInitialState(nextProps) {
    if (nextProps && nextProps.edit && nextProps.source) {
      this.setState(Object.assign({ ...this.initialState }, { source: nextProps.source }));
    } else {
      this.setState(Object.assign({ ...this.initialState }));
    }
  }

  onCancel() {
    const { fulfilled, error } = this.state;

    const closeWizard = () => {
      Store.dispatch({
        type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
      });

      Store.dispatch({
        type: sourcesTypes.UPDATE_SOURCE_HIDE
      });
    };

    if (fulfilled || error) {
      closeWizard();
    } else {
      Store.dispatch({
        type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
        title: 'Cancel Add Source',
        heading: 'Are you sure you want to exit this wizard?',
        body: 'Exiting this wizard will cancel adding the source.',
        cancelButtonText: 'No',
        confirmButtonText: 'Yes',
        onConfirm: closeWizard
      });
    }
  }

  onStep(stepIndex) {
    // ToDo: wizard step map/breadcrumb/trail click, or leave disabled
  }

  onNext() {
    const { activeStepIndex } = this.state;
    const numberSteps = addSourceWizardSteps.length;

    if (activeStepIndex < numberSteps - 1) {
      this.setState({ activeStepIndex: activeStepIndex + 1 });
    }
  }

  onBack() {
    let { activeStepIndex } = this.state;

    if (activeStepIndex >= 1) {
      this.setState({ activeStepIndex: activeStepIndex - 1 });
    }
  }

  onSubmit(event) {
    const { addSource, updateSource } = this.props;
    const { stepOneValid, stepTwoValid, source, edit } = this.state;

    if (stepOneValid && stepTwoValid) {
      if (edit) {
        updateSource(source.id, source).finally(() => {
          this.setState({ activeStepIndex: 2 });
        });
      } else {
        addSource(source).finally(() => {
          this.setState({ activeStepIndex: 2 });
        });
      }
    }
  }

  renderWizardSteps() {
    const { activeStepIndex } = this.state;
    const wizardSteps = addSourceWizardSteps;
    const activeStep = wizardSteps[activeStepIndex];

    return wizardSteps.map((step, stepIndex) => {
      return (
        <Wizard.Step
          key={stepIndex}
          stepIndex={stepIndex}
          step={step.step}
          label={step.label}
          title={step.title}
          activeStep={activeStep && activeStep.step}
          onClick={e => this.onStep(activeStep && activeStep.step)}
        />
      );
    });
  }

  // ToDo: Final wizard step needs additional spinner animation, copy/error messaging for submit failures.
  render() {
    const { show } = this.props;
    const { activeStepIndex, stepOneValid, stepTwoValid } = this.state;
    const wizardSteps = addSourceWizardSteps;

    return (
      <React.Fragment>
        <CreateCredentialDialog />
        <Modal show={show} onHide={this.onCancel} dialogClassName="modal-dialog modal-lg wizard-pf quipucords-wizard">
          <Wizard>
            <Modal.Header>
              <button className="close" onClick={this.onCancel} aria-hidden="true" aria-label="Close">
                <Icon type="pf" name="close" />
              </button>
              <Modal.Title>Add Source</Modal.Title>
            </Modal.Header>
            <Modal.Body className="wizard-pf-body clearfix">
              <Wizard.Steps steps={this.renderWizardSteps()} />
              <Wizard.Row>
                <Wizard.Main>
                  {wizardSteps.map((step, stepIndex) => {
                    return (
                      <Wizard.Contents key={step.title} stepIndex={stepIndex} activeStepIndex={activeStepIndex}>
                        {stepIndex === 0 && <AddSourceWizardStepOne />}
                        {stepIndex === 1 && <AddSourceWizardStepTwo />}
                        {stepIndex === 2 && <AddSourceWizardStepThree />}
                      </Wizard.Contents>
                    );
                  })}
                </Wizard.Main>
              </Wizard.Row>
            </Modal.Body>
            <Modal.Footer className="wizard-pf-footer">
              <Button bsStyle="default" className="btn-cancel" disabled={activeStepIndex === 2} onClick={this.onCancel}>
                Cancel
              </Button>
              <Button bsStyle="default" disabled={activeStepIndex === 0 || activeStepIndex === 2} onClick={this.onBack}>
                <Icon type="fa" name="angle-left" />Back
              </Button>
              {activeStepIndex === 0 && (
                <Button bsStyle="primary" disabled={!stepOneValid} onClick={this.onNext}>
                  Next<Icon type="fa" name="angle-right" />
                </Button>
              )}
              {activeStepIndex === 1 && (
                <Button bsStyle="primary" disabled={!stepTwoValid} onClick={this.onSubmit}>
                  Save<Icon type="fa" name="angle-right" />
                </Button>
              )}
              {activeStepIndex === 2 && (
                <Button bsStyle="primary" disabled={!stepTwoValid} onClick={this.onCancel}>
                  Close
                </Button>
              )}
            </Modal.Footer>
          </Wizard>
        </Modal>
      </React.Fragment>
    );
  }
}

AddSourceWizard.propTypes = {
  addSource: PropTypes.func,
  updateSource: PropTypes.func,
  show: PropTypes.bool.isRequired,
  source: PropTypes.object,
  stepOneValid: PropTypes.bool,
  stepTwoValid: PropTypes.bool,
  fulfilled: PropTypes.bool,
  error: PropTypes.bool,
  errorMessage: PropTypes.string
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  addSource: data => dispatch(addSource(data)),
  updateSource: (id, data) => dispatch(updateSource(id, data))
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.addSourceWizard.view);
};

export default connect(mapStateToProps, mapDispatchToProps)(AddSourceWizard);
