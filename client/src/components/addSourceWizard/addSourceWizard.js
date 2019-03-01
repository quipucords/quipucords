import React from 'react';
import PropTypes from 'prop-types';
import { Button, Icon, Wizard } from 'patternfly-react';
import { connect, reduxActions, reduxTypes, store } from '../../redux';
import { addSourceWizardSteps, editSourceWizardSteps } from './addSourceWizardConstants';
import helpers from '../../common/helpers';
import apiTypes from '../../constants/apiConstants';

class AddSourceWizard extends React.Component {
  state = {
    activeStepIndex: 0
  };

  onCancel = () => {
    const { edit, errorStatus, fulfilled, pending } = this.props;

    const closeWizard = () => {
      this.setState({ activeStepIndex: 0 }, () => {
        store.dispatch({
          type: reduxTypes.confirmationModal.CONFIRMATION_MODAL_HIDE
        });

        store.dispatch({
          type: reduxTypes.sources.UPDATE_SOURCE_HIDE
        });

        if (fulfilled) {
          store.dispatch({
            type: reduxTypes.sources.UPDATE_SOURCES
          });
        }
      });
    };

    if (fulfilled || errorStatus >= 500 || errorStatus === 0) {
      closeWizard();
    } else if (pending) {
      store.dispatch({
        type: reduxTypes.confirmationModal.CONFIRMATION_MODAL_SHOW,
        title: `Exit Wizard`,
        heading: 'Are you sure you want to exit this wizard?',
        body: `The wizard is in a pending state and will continue ${edit ? 'updating' : 'adding'} this source.`,
        cancelButtonText: 'No',
        confirmButtonText: 'Yes',
        onConfirm: closeWizard
      });
    } else {
      store.dispatch({
        type: reduxTypes.confirmationModal.CONFIRMATION_MODAL_SHOW,
        title: 'Cancel Add Source',
        heading: `Are you sure you want to cancel ${edit ? 'updating' : 'adding'} this source?`,
        cancelButtonText: 'No',
        confirmButtonText: 'Yes',
        onConfirm: closeWizard
      });
    }
  };

  onNext = () => {
    const { activeStepIndex } = this.state;
    const { addSteps, edit, editSteps } = this.props;
    const wizardStepsLength = edit ? editSteps.length : addSteps.length;

    if (activeStepIndex < wizardStepsLength - 1) {
      this.setState({ activeStepIndex: activeStepIndex + 1 });
    }
  };

  onBack = () => {
    const { activeStepIndex } = this.state;

    if (activeStepIndex >= 1) {
      this.setState({ activeStepIndex: activeStepIndex - 1 });
    }
  };

  onSubmit = () => {
    const { addSource, edit, source, stepOneValid, stepTwoValid, updateSource } = this.props;
    const { activeStepIndex } = this.state;

    if (stepOneValid && stepTwoValid) {
      this.setState({ activeStepIndex: activeStepIndex + 1 }, () => {
        let addUpdateSourcePromise;

        if (edit) {
          addUpdateSourcePromise = updateSource(source[apiTypes.API_SUBMIT_SOURCE_ID], source);
        } else {
          addUpdateSourcePromise = addSource(source, { scan: true });
        }

        addUpdateSourcePromise.then(
          () => {
            const { props } = this;

            if (!props.show) {
              store.dispatch({
                type: reduxTypes.toastNotifications.TOAST_ADD,
                alertType: 'success',
                message: `Source ${source[apiTypes.API_SUBMIT_SOURCE_NAME]} was ${(props.edit && 'updated') ||
                  'created'}`
              });
            }
          },
          () => {
            const { props } = this;

            if (!props.show) {
              store.dispatch({
                type: reduxTypes.toastNotifications.TOAST_ADD,
                alertType: 'error',
                header: `Error ${(props.edit && 'updating') || 'creating'} source`,
                message: props.errorMessage
              });
            }
          }
        );
      });
    }
  };

  onStep = () => {
    // ToDo: wizard step map/breadcrumb/trail click, or leave disabled
  };

  renderWizardSteps() {
    const { activeStepIndex } = this.state;
    const { addSteps, edit, editSteps } = this.props;
    const wizardSteps = edit ? editSteps : addSteps;
    const activeStep = wizardSteps[activeStepIndex];

    return wizardSteps.map((step, stepIndex) => (
      <Wizard.Step
        key={step.title}
        stepIndex={stepIndex}
        step={step.step}
        label={step.label}
        title={step.title}
        activeStep={activeStep && activeStep.step}
      />
    ));
  }

  render() {
    const {
      addSteps,
      edit,
      editSteps,
      error,
      errorStatus,
      fulfilled,
      pending,
      show,
      stepOneValid,
      stepTwoValid
    } = this.props;
    const { activeStepIndex } = this.state;
    const wizardSteps = edit ? editSteps : addSteps;

    if (!show) {
      return null;
    }

    return (
      <Wizard show={show}>
        <Wizard.Header onClose={this.onCancel} title={edit ? 'Edit Source' : 'Add Source'} />
        <Wizard.Body>
          <Wizard.Steps steps={this.renderWizardSteps()} />
          <Wizard.Row>
            <Wizard.Main>
              {wizardSteps.map((step, stepIndex) => (
                <Wizard.Contents key={step.title} stepIndex={stepIndex} activeStepIndex={activeStepIndex}>
                  {wizardSteps[stepIndex].page}
                </Wizard.Contents>
              ))}
            </Wizard.Main>
          </Wizard.Row>
        </Wizard.Body>
        <Wizard.Footer>
          <Button bsStyle="default" className="btn-cancel" disabled={fulfilled} onClick={this.onCancel}>
            Cancel
          </Button>
          <Button
            bsStyle="default"
            disabled={activeStepIndex === 0 || errorStatus >= 500 || errorStatus === 0 || pending || fulfilled}
            onClick={this.onBack}
          >
            <Icon type="fa" name="angle-left" />
            Back
          </Button>
          {activeStepIndex < wizardSteps.length - 2 && (
            <Button bsStyle="primary" disabled={!stepOneValid} onClick={this.onNext}>
              Next
              <Icon type="fa" name="angle-right" />
            </Button>
          )}
          {activeStepIndex === wizardSteps.length - 2 && (
            <Button bsStyle="primary" disabled={!stepTwoValid || pending} onClick={this.onSubmit}>
              Save
              <Icon type="fa" name="angle-right" />
            </Button>
          )}
          {activeStepIndex === wizardSteps.length - 1 && (
            <Button bsStyle="primary" disabled={error || pending} onClick={this.onCancel}>
              Close
            </Button>
          )}
        </Wizard.Footer>
      </Wizard>
    );
  }
}

AddSourceWizard.propTypes = {
  addSource: PropTypes.func,
  addSteps: PropTypes.array,
  updateSource: PropTypes.func,
  show: PropTypes.bool.isRequired,
  edit: PropTypes.bool,
  editSteps: PropTypes.array,
  error: PropTypes.bool,
  errorMessage: PropTypes.string, // eslint-disable-line
  errorStatus: PropTypes.number,
  fulfilled: PropTypes.bool,
  pending: PropTypes.bool,
  source: PropTypes.object,
  stepOneValid: PropTypes.bool,
  stepTwoValid: PropTypes.bool
};

AddSourceWizard.defaultProps = {
  addSource: helpers.noop,
  addSteps: addSourceWizardSteps,
  updateSource: helpers.noop,
  edit: false,
  editSteps: editSourceWizardSteps,
  error: false,
  errorMessage: null,
  errorStatus: null,
  fulfilled: false,
  pending: false,
  source: {},
  stepOneValid: false,
  stepTwoValid: false
};

const mapDispatchToProps = dispatch => ({
  addSource: (data, query) => dispatch(reduxActions.sources.addSource(data, query)),
  updateSource: (id, data) => dispatch(reduxActions.sources.updateSource(id, data))
});

const mapStateToProps = state => ({ ...state.addSourceWizard });

const ConnectedAddSourceWizard = connect(
  mapStateToProps,
  mapDispatchToProps
)(AddSourceWizard);

export { ConnectedAddSourceWizard as default, ConnectedAddSourceWizard, AddSourceWizard };
