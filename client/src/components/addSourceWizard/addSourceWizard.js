import React from 'react';
import PropTypes from 'prop-types';
import { Button, Icon, Wizard } from 'patternfly-react';
import { connect } from 'react-redux';
import Store from '../../redux/store';
import { confirmationModalTypes, sourcesTypes } from '../../redux/constants';
import { addSourceWizardSteps, editSourceWizardSteps } from './addSourceWizardConstants';
import { reduxActions } from '../../redux/actions';
import helpers from '../../common/helpers';

class AddSourceWizard extends React.Component {
  constructor(props) {
    super(props);

    this.initialState = {
      activeStepIndex: 0,
      stepOneValid: false,
      stepTwoValid: false
    };

    this.state = { ...this.initialState };
  }

  componentWillReceiveProps(nextProps) {
    const { show } = this.props;

    if (!show && nextProps.show) {
      this.resetInitialState(nextProps);
    }

    this.setState({
      stepOneValid: nextProps.stepOneValid || false,
      stepTwoValid: nextProps.stepTwoValid || false
    });
  }

  onCancel = () => {
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
        heading: 'Are you sure you want to cancel adding this source?',
        cancelButtonText: 'No',
        confirmButtonText: 'Yes',
        onConfirm: closeWizard
      });
    }
  };

  onStep = () => {
    // ToDo: wizard step map/breadcrumb/trail click, or leave disabled
  };

  onNext = () => {
    const { activeStepIndex } = this.state;
    const { edit } = this.props;
    const numberSteps = edit ? editSourceWizardSteps.length : addSourceWizardSteps.length;

    if (activeStepIndex < numberSteps - 1) {
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
  };

  resetInitialState(nextProps) {
    if (nextProps && nextProps.edit && nextProps.source) {
      this.setState(Object.assign({ ...this.initialState }, { source: nextProps.source }));
    } else {
      this.setState(Object.assign({ ...this.initialState }));
    }
  }

  renderWizardSteps() {
    const { activeStepIndex } = this.state;
    const { edit } = this.props;
    const wizardSteps = edit ? editSourceWizardSteps : addSourceWizardSteps;
    const activeStep = wizardSteps[activeStepIndex];

    return wizardSteps.map((step, stepIndex) => (
      <Wizard.Step
        key={step.title}
        stepIndex={stepIndex}
        step={step.step}
        label={step.label}
        title={step.title}
        activeStep={activeStep && activeStep.step}
        onClick={() => this.onStep(activeStep && activeStep.step)}
      />
    ));
  }

  render() {
    const { show, edit } = this.props;
    const { activeStepIndex, stepOneValid, stepTwoValid } = this.state;
    const wizardSteps = edit ? editSourceWizardSteps : addSourceWizardSteps;

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
            <Button bsStyle="primary" disabled={!stepTwoValid} onClick={this.onSubmit}>
              Save
              <Icon type="fa" name="angle-right" />
            </Button>
          )}
          {activeStepIndex === wizardSteps.length - 1 && (
            <Button bsStyle="primary" disabled={!stepTwoValid} onClick={this.onCancel}>
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
  updateSource: PropTypes.func,
  show: PropTypes.bool.isRequired,
  edit: PropTypes.bool,
  source: PropTypes.object,
  stepOneValid: PropTypes.bool,
  stepTwoValid: PropTypes.bool,
  fulfilled: PropTypes.bool,
  error: PropTypes.bool
};

AddSourceWizard.defaultProps = {
  addSource: helpers.noop,
  updateSource: helpers.noop,
  edit: false,
  source: {},
  stepOneValid: false,
  stepTwoValid: false,
  fulfilled: false,
  error: false
};

const mapDispatchToProps = dispatch => ({
  addSource: (data, query) => dispatch(reduxActions.sources.addSource(data, query)),
  updateSource: (id, data) => dispatch(reduxActions.sources.updateSource(id, data))
});

const mapStateToProps = state => ({ ...state.addSourceWizard.view });

const ConnectedAddSourceWizard = connect(
  mapStateToProps,
  mapDispatchToProps
)(AddSourceWizard);

export { ConnectedAddSourceWizard as default, ConnectedAddSourceWizard, AddSourceWizard };
