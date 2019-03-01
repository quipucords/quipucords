import React from 'react';
import PropTypes from 'prop-types';
import { Icon, Spinner } from 'patternfly-react';
import { connect, reduxSelectors } from '../../redux';

const AddSourceWizardStepThree = ({ add, error, fulfilled, pending, name }) => (
  <React.Fragment>
    {error && (
      <div className="wizard-pf-complete blank-slate-pf">
        <div className="wizard-pf-success-icon">
          <Icon type="pf" name="error-circle-o" />
        </div>
        <h3 className="blank-slate-pf-main-action">Error {add ? 'Creating' : 'Updating'} Source</h3>
        <p className="blank-slate-pf-secondary-action">There are errors on the previous step</p>
      </div>
    )}
    {fulfilled && (
      <div className="wizard-pf-complete blank-slate-pf">
        <div className="wizard-pf-success-icon">
          <Icon type="pf" name="ok" />
        </div>
        <h3 className="blank-slate-pf-main-action">
          <strong>{name}</strong> was {add ? 'created' : 'updated'}.
        </h3>
      </div>
    )}
    {pending && (
      <div className="wizard-pf-process blank-slate-pf">
        <Spinner loading size="lg" className="blank-slate-pf-icon" />
        <h3 className="blank-slate-pf-main-action">{add ? 'Creating' : 'Updating'} Source...</h3>
        <p className="blank-slate-pf-secondary-action">
          Please wait while source <strong>{name}</strong> is being {add ? 'created' : 'updated'}.
        </p>
      </div>
    )}
  </React.Fragment>
);

AddSourceWizardStepThree.propTypes = {
  add: PropTypes.bool,
  error: PropTypes.bool,
  fulfilled: PropTypes.bool,
  pending: PropTypes.bool,
  name: PropTypes.string
};

AddSourceWizardStepThree.defaultProps = {
  add: false,
  error: false,
  fulfilled: false,
  pending: false,
  name: null
};

const makeMapStateToProps = () => {
  const mapSource = reduxSelectors.sources.makeSourceDetail();

  return (state, props) => ({
    ...state.addSourceWizard,
    ...mapSource(state, props)
  });
};

const ConnectedAddSourceWizardStepThree = connect(makeMapStateToProps)(AddSourceWizardStepThree);

export { ConnectedAddSourceWizardStepThree as default, ConnectedAddSourceWizardStepThree, AddSourceWizardStepThree };
