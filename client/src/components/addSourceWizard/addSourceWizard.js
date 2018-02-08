import React from 'react';
import PropTypes from 'prop-types';
import { Modal, Button, Icon, Wizard } from 'patternfly-react';
import helpers from '../../common/helpers';
import { addSourceWizardSteps } from './addSourceWizardConstants';
import { connect } from 'react-redux'
import { confirmationModalTypes, sourcesTypes } from '../../redux/constants'
import Store from '../../redux/store'

class AddSourceWizard extends React.Component {
  constructor(props) {
    super(props);

    this.initialState = {
      activeStepIndex: 0,
      stepOneValid: true,
      stepTwoValid: true,
      stepThreeValid: true,
    };

    this.state = { ...this.initialState };

    helpers.bindMethods(this, [
      'onCancel',
      'onStep',
      'onNext',
      'onBack',
      'onSubmit',
      'onReset'
    ]);
  }

  componentWillReceiveProps(nextProps) {}

  onCancel() {
    let onConfirm = () => {
      Store.dispatch({
        type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
      });

      Store.dispatch({
        type: sourcesTypes.UPDATE_SOURCE_HIDE
      });
    };

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Cancel Add Source',
      heading: 'Are you sure you want to exit this wizard?',
      body: 'Exiting this wizard will cancel adding the source.',
      cancelButtonText: 'No',
      confirmButtonText: 'Yes',
      onConfirm: onConfirm
    });
  }

  onStep(stepIndex) {
    if (stepIndex === this.state.activeStepIndex) {
      return;
    }

    this.setState({
      activeStepIndex: stepIndex
    });
  }

  onNext() {
    const numberSteps = addSourceWizardSteps.length;
    let { activeStepIndex } = this.state;

    if (activeStepIndex < numberSteps - 1) {
      this.setState({ activeStepIndex: (activeStepIndex += 1) });
    }
  }

  onBack() {
    let { activeStepIndex } = this.state;

    if (activeStepIndex >= 1) {
      this.setState({ activeStepIndex: (activeStepIndex -= 1) });
    }
  }

  onSubmit() {}

  onReset() {}

  renderWizardContent(wizardSteps, activeStepIndex) {
    return wizardSteps.map((step, stepIndex) => {
      let stepContent;

      switch (stepIndex) {
        case 0:
          stepContent = <div className="form-group required">Step One</div>;
          break;
        case 1:
          stepContent = <div className="form-group required">Step Two</div>;
          break;
        case 2:
          stepContent = <div className="form-group required">Step Three</div>;
          break;
        default:
          stepContent = null;
          break;
      }

      return (
        <Wizard.Contents
          key={step.title}
          stepIndex={stepIndex}
          activeStepIndex={activeStepIndex}
        >
          {stepContent}
        </Wizard.Contents>
      );
    });
  }

  renderWizardSteps(wizardSteps, activeStepIndex, onStep) {
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
          onClick={onStep || helpers.noop}
        />
      );
    });
  }

  render() {
    const { show } = this.props;
    const {
      activeStepIndex,
      stepOneValid,
      stepTwoValid,
      stepThreeValid
    } = this.state;

    return (
      <Modal
        show={show}
        onHide={this.onCancel}
        dialogClassName="modal-dialog modal-lg wizard-pf"
      >
        <Wizard>
          <Modal.Header>
            <button
              className="close"
              onClick={this.onCancel}
              aria-hidden="true"
              aria-label="Close"
            >
              <Icon type="pf" name="close" />
            </button>
            <Modal.Title>Add Source</Modal.Title>
          </Modal.Header>
          <Modal.Body className="wizard-pf-body clearfix">
            <Wizard.Steps
              steps={this.renderWizardSteps(
                addSourceWizardSteps,
                activeStepIndex,
                this.onStep
              )}
            />
            <Wizard.Row>
              <Wizard.Main>
                {this.renderWizardContent(
                  addSourceWizardSteps,
                  activeStepIndex
                )}
              </Wizard.Main>
            </Wizard.Row>
          </Modal.Body>
          <Modal.Footer className="wizard-pf-footer">
            <Button
              bsStyle="default"
              className="btn-cancel"
              onClick={this.onCancel}
            >
              Cancel
            </Button>
            <Button
              bsStyle="default"
              disabled={activeStepIndex === 0}
              onClick={this.onBack}
            >
              <Icon type="fa" name="angle-left" />Back
            </Button>
            {activeStepIndex === 0 && (
              <Button
                bsStyle="primary"
                disabled={!stepOneValid}
                onClick={this.onNext}
              >
                Next<Icon type="fa" name="angle-right" />
              </Button>
            )}
            {activeStepIndex === 1 && (
              <Button
                bsStyle="primary"
                disabled={!stepTwoValid}
                onClick={this.onNext}
              >
                Next<Icon type="fa" name="angle-right" />
              </Button>
            )}
            {activeStepIndex === 2 && (
              <Button
                bsStyle="primary"
                disabled={!stepThreeValid}
                onClick={this.onSubmit}
              >
                Next<Icon type="fa" name="angle-right" />
              </Button>
            )}
          </Modal.Footer>
        </Wizard>
      </Modal>
    );
  }
}

AddSourceWizard.propTypes = {
  show: PropTypes.bool.isRequired
};

const mapDispatchToProps = (dispatch, ownProps) => ({
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.sources.update);
};

export default connect(mapStateToProps, mapDispatchToProps)(AddSourceWizard);
