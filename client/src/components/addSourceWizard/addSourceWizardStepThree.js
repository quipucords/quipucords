import React from 'react';
import PropTypes from 'prop-types';
import { apiTypes } from '../../constants';
import { connect } from 'react-redux';

const AddSourceWizardStepThree = ({ source }) => {
  return (
    <div>
      <p>Searching {source[apiTypes.API_SOURCE_TYPE]} for hosts...</p>
      <p>You can dismiss this and receive a notification when the search is complete.</p>
    </div>
  );
};

AddSourceWizardStepThree.propTypes = {
  source: PropTypes.object
};

const mapStateToProps = function(state) {
  return Object.assign({}, state.addSourceWizard.view);
};

export default connect(mapStateToProps)(AddSourceWizardStepThree);
