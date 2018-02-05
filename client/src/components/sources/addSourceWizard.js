import React from 'react';
import PropTypes from 'prop-types';
import { Modal, Button, Icon, Wizard } from 'patternfly-react';
import { noop, bindMethods } from '../../common/helpers';
import { AddSourceWizardSteps } from './addSourceWizardConstants';

class AddSourceWizard extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      activeStepIndex: props.initialStepIndex || 0
    };

    bindMethods(this, [
      'confirm',
      'onStepClick',
      'onNextButtonClick',
      'onBackButtonClick'
    ]);
  }

  componentWillReceiveProps(nextProps) {}

  onStepClick(stepIndex) {
    if (stepIndex === this.state.activeStepIndex) {
      return;
    }

    this.setState({
      activeStepIndex: stepIndex
    });
  }

  onNextButtonClick() {}

  onBackButtonClick() {}

  confirm() {}

  renderWizardSteps(wizardSteps, activeStepIndex, onStepClick) {
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
          onClick={onStepClick || noop}
        />
      );
    });
  }

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

  render() {
    const { show, onCancel } = this.props;
    const { activeStepIndex } = this.state;

    return (
      <form className="form-horizontal">
        <Modal
          show={show}
          onHide={onCancel}
          dialogClassName="modal-dialog modal-lg wizard-pf"
        >
          <Wizard>
            <Modal.Header>
              <button
                className="close"
                onClick={onCancel}
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
                  AddSourceWizardSteps,
                  activeStepIndex,
                  this.onStepClick
                )}
              />
              <Wizard.Row>
                <Wizard.Main>
                  {this.renderWizardContent(
                    AddSourceWizardSteps,
                    activeStepIndex
                  )}
                </Wizard.Main>
              </Wizard.Row>
            </Modal.Body>
            <Modal.Footer className="wizard-pf-footer">
              <Button
                bsStyle="default"
                className="btn-cancel"
                onClick={onCancel}
              >
                Cancel
              </Button>
              <Button bsStyle="default" disabled>
                <Icon type="fa" name="angle-left" />Back
              </Button>
              <Button bsStyle="primary" disabled>
                Next<Icon type="fa" name="angle-right" />
              </Button>
            </Modal.Footer>
          </Wizard>
        </Modal>
      </form>
    );
  }
}

AddSourceWizard.propTypes = {
  show: PropTypes.bool.isRequired,
  initialStepIndex: PropTypes.number,
  onCancel: PropTypes.func
};

export { AddSourceWizard };
