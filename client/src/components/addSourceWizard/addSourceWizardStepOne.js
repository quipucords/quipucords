import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Form, Radio } from 'patternfly-react';
import Store from '../../redux/store';
import helpers from '../../common/helpers';
import { apiTypes } from '../../constants';
import { sourcesTypes } from '../../redux/constants';
import _ from 'lodash';

class AddSourceWizardStepOne extends React.Component {
  constructor(props) {
    super(props);

    this.initialState = {
      sourceType: '',
      sourceTypeError: null
    };

    this.state = { ...this.initialState };

    helpers.bindMethods(this, ['onChangeSourceType']);
  }

  componentDidMount() {
    this.setState({ ...this.initializeState(this.props) }, () => {
      this.validateStep();
    });
  }

  initializeState(nextProps) {
    return {
      sourceType: _.get(nextProps, ['source', apiTypes.API_SOURCE_TYPE], 'network')
    };
  }

  validateStep() {
    const { sourceType } = this.state;
    const { source } = this.props;

    if (sourceType !== '') {
      Store.dispatch({
        type: sourcesTypes.UPDATE_SOURCE_WIZARD_STEPONE,
        source: _.merge({}, source, { [apiTypes.API_SOURCE_TYPE]: sourceType })
      });
    }
  }

  onChangeSourceType(event) {
    this.setState(
      {
        sourceType: event.target.value
      },
      () => this.validateStep()
    );
  }

  render() {
    const { sourceType, sourceTypeError } = this.state;

    return (
      <Form horizontal>
        <h3 className="right-aligned_basic-form">Select source type</h3>
        <Form.FormGroup validationState={sourceTypeError ? 'error' : null}>
          <Radio
            name="sourceType"
            value="network"
            checked={sourceType === 'network'}
            onChange={this.onChangeSourceType}
          >
            Network Range
          </Radio>
          <Radio
            name="sourceType"
            value="satellite"
            checked={sourceType === 'satellite'}
            onChange={this.onChangeSourceType}
          >
            Satellite
          </Radio>
          <Radio
            name="sourceType"
            value="vcenter"
            checked={sourceType === 'vcenter'}
            onChange={this.onChangeSourceType}
          >
            vCenter Server
          </Radio>
        </Form.FormGroup>
      </Form>
    );
  }
}

AddSourceWizardStepOne.propTypes = {
  source: PropTypes.object
};

const mapStateToProps = function(state) {
  return { ...state.addSourceWizard.view };
};

export default connect(mapStateToProps)(AddSourceWizardStepOne);
