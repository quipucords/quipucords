import React from 'react';
import PropTypes from 'prop-types';
import { Modal, Button, Icon, Wizard } from 'patternfly-react';
import helpers from '../../common/helpers';
import { connect } from 'react-redux';
import Store from '../../redux/store';
import { confirmationModalTypes, sourcesTypes } from '../../redux/constants';
import { addSourceWizardSteps, editSourceWizardSteps } from './addSourceWizardConstants';
import { addSource, updateSource } from '../../redux/actions/sourcesActions';

class AddSourceWizard extends React.Component {
  constructor(props) {
    super(props);

    this.initialState = {
      activeStepIndex: 0,
      stepOneValid: false,
      stepTwoValid: false
    };

    this.state = { ...this.initialState };

    helpers.bindMethods(this, ['onCancel', 'onStep', 'onNext', 'onBack', 'onSubmit']);
  }

  componentWillReceiveProps(nextProps) {
    if (!this.props.show && nextProps.show) {
      this.resetInitialState(nextProps);
    }

    this.setState({
      stepOneValid: nextProps.stepOneValid || false,
      stepTwoValid: nextProps.stepTwoValid || false
    });
  }

  resetInitialState(nextProps) {
    if (nextProps && nextProps.edit && nextProps.source) {
      this.setState(Object.assign({ ...this.initialState }, { source: nextProps.source }));
    } else {
      this.setState(Object.assign({ ...this.initialState }));
    }
  }

  onCancel() {
    const { fulfilled, error } = this.props;

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
    const { edit } = this.props;
    const numberSteps = edit ? editSourceWizardSteps.length : addSourceWizardSteps.length;

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
    const { addSource, updateSource, source, edit } = this.props;
    const { stepOneValid, stepTwoValid } = this.state;

    if (stepOneValid && stepTwoValid) {
      if (edit) {
        const update = {
          name: source.name,
          hosts: source.hosts,
          port: source.port,
          credentials: source.credentials,
          options: source.options
        };

        updateSource(source.id, update).finally(() => {
          this.setState({ activeStepIndex: 1 });
        });
      } else {
        addSource(source, { scan: true }).finally(() => {
          this.setState({ activeStepIndex: 2 });
        });
      }
    }
  }

  renderWizardSteps() {
    const { activeStepIndex } = this.state;
    const { edit } = this.props;
    const wizardSteps = edit ? editSourceWizardSteps : addSourceWizardSteps;
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

  render() {
    const { show, edit } = this.props;
    const { activeStepIndex, stepOneValid, stepTwoValid } = this.state;
    const wizardSteps = edit ? editSourceWizardSteps : addSourceWizardSteps;

    return (
      <React.Fragment>
        <Modal show={show} onHide={this.onCancel} dialogClassName="modal-dialog modal-lg wizard-pf quipucords-wizard">
          <Wizard>
            <Modal.Header>
              <button className="close" onClick={this.onCancel} aria-hidden="true" aria-label="Close">
                <Icon type="pf" name="close" />
              </button>
              <Modal.Title>{edit ? 'Edit' : 'Add'} Source</Modal.Title>
            </Modal.Header>
            <Modal.Body className="wizard-pf-body clearfix">
              <Wizard.Steps steps={this.renderWizardSteps()} />
              <Wizard.Row>
                <Wizard.Main>
                  {wizardSteps.map((step, stepIndex) => {
                    return (
                      <Wizard.Contents key={step.title} stepIndex={stepIndex} activeStepIndex={activeStepIndex}>
                        {wizardSteps[stepIndex].page}
                      </Wizard.Contents>
                    );
                  })}
                </Wizard.Main>
              </Wizard.Row>
            </Modal.Body>
            <Modal.Footer className="wizard-pf-footer">
              <Button
                bsStyle="default"
                className="btn-cancel"
                disabled={activeStepIndex === wizardSteps.length - 1}
                onClick={this.onCancel}
              >
                Cancel
              </Button>
              <Button
                bsStyle="default"
                disabled={activeStepIndex === 0 || activeStepIndex === wizardSteps.length - 1}
                onClick={this.onBack}
              >
                <Icon type="fa" name="angle-left" />Back
              </Button>
              {activeStepIndex < wizardSteps.length - 2 && (
                <Button bsStyle="primary" disabled={!stepOneValid} onClick={this.onNext}>
                  Next<Icon type="fa" name="angle-right" />
                </Button>
              )}
              {activeStepIndex === wizardSteps.length - 2 && (
                <Button bsStyle="primary" disabled={!stepTwoValid} onClick={this.onSubmit}>
                  Save<Icon type="fa" name="angle-right" />
                </Button>
              )}
              {activeStepIndex === wizardSteps.length - 1 && (
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
  edit: PropTypes.bool,
  source: PropTypes.object,
  stepOneValid: PropTypes.bool,
  stepTwoValid: PropTypes.bool,
  fulfilled: PropTypes.bool,
  error: PropTypes.bool
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  addSource: (data, query) => dispatch(addSource(data, query)),
  updateSource: (id, data) => dispatch(updateSource(id, data))
});

const mapStateToProps = function(state) {
  return { ...state.addSourceWizard.view };
};

export default connect(mapStateToProps, mapDispatchToProps)(AddSourceWizard);
