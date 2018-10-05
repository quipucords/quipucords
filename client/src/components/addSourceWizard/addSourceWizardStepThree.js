import React from 'react';
import PropTypes from 'prop-types';
import { Spinner } from 'patternfly-react';
import { connect } from 'react-redux';

const AddSourceWizardStepThree = ({ view }) => {
  if (view.error) {
    return (
      <div className="wizard-pf-complete blank-slate-pf">
        <div className="wizard-pf-success-icon">
          <span className="pficon pficon-error-circle-o" />
        </div>
        <h3 className="blank-slate-pf-main-action">Error {view.add ? 'Creating' : 'Updating'} Source</h3>
        <p className="blank-slate-pf-secondary-action">{view.errorMessage}</p>
      </div>
    );
  }

  if (!view.fulfilled) {
    return (
      <div className="wizard-pf-process blank-slate-pf">
        <Spinner loading size="lg" className="blank-slate-pf-icon" />
        <h3 className="blank-slate-pf-main-action">{view.add ? 'Creating' : 'Updating'} Source...</h3>
        <p className="blank-slate-pf-secondary-action">
          Please wait while source is being {view.add ? 'created' : 'updated'}.
        </p>
      </div>
    );
  }

  return (
    <div className="wizard-pf-complete blank-slate-pf">
      <div className="wizard-pf-success-icon">
        <span className="glyphicon glyphicon-ok-circle" />
      </div>
      <h3 className="blank-slate-pf-main-action">
        <strong>{view.source.name}</strong> was {view.add ? 'created' : 'updated'}.
      </h3>
    </div>
  );
};

AddSourceWizardStepThree.propTypes = {
  view: PropTypes.object
};

const mapStateToProps = function(state) {
  return Object.assign({}, { view: state.addSourceWizard.view });
};

export default connect(mapStateToProps)(AddSourceWizardStepThree);
