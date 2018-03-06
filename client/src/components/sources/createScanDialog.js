import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Alert, Modal, Button, Form, Grid, Icon } from 'patternfly-react';

import helpers from '../../common/helpers';
import Store from '../../redux/store';
import { addScan } from '../../redux/actions/scansActions';
import { scansTypes, toastNotificationTypes } from '../../redux/constants';

class CreateScanDialog extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['updateScanName', 'createScan']);
    this.state = {
      scanName: '',
      validScanName: false
    };
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.show && !this.props.show) {
      this.setState({ scanName: '', validScanName: false });
      Store.dispatch({
        type: scansTypes.ADD_SCAN_RESET_STATUS
      });
    }
    if (
      this.props.show &&
      _.get(nextProps, 'action.add') &&
      _.get(nextProps, 'action.fulfilled') &&
      !_.get(this.props, 'action.fulfilled')
    ) {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'success',
        message: (
          <span>
            Created new scan <strong>{this.state.scanName}</strong>.
          </span>
        )
      });
      this.props.onClose(true);
    }
  }

  createScan() {
    const { sources, addScan } = this.props;
    const { scanName } = this.state;

    let data = {
      name: scanName,
      sources: sources.map(item => item.id)
    };

    addScan(data);
  }

  validateScanName(scanName) {
    return scanName && scanName.length > 0;
  }

  updateScanName(event) {
    this.setState({
      scanName: event.target.value,
      validScanName: this.validateScanName(event.target.value)
    });
  }

  onScanNameKeyPress(keyEvent) {
    const { scanName, validScanName } = this.state;

    if (keyEvent.key === 'Enter' && scanName && validScanName) {
      keyEvent.stopPropagation();
      keyEvent.preventDefault();
      this.createScan();
    }
  }

  errorDismissed() {
    Store.dispatch({
      type: scansTypes.ADD_SCAN_RESET_STATUS
    });
  }

  renderErrorMessage() {
    const { action } = this.props;

    if (action.error) {
      return (
        <Alert type="error" onDismiss={this.errorDismissed}>
          <strong>Error</strong> {action.errorMessage}
        </Alert>
      );
    } else {
      return null;
    }
  }

  render() {
    const { show, sources, onClose } = this.props;
    const { scanName, validScanName } = this.state;

    if (!sources || sources.length === 0 || !sources[0]) {
      return null;
    }

    return (
      <Modal show={show} onHide={onClose}>
        <Modal.Header>
          <button className="close" onClick={onClose} aria-hidden="true" aria-label="Close">
            <Icon type="pf" name="close" />
          </button>
          <Modal.Title>Scan</Modal.Title>
        </Modal.Header>
        <Modal.Body />
        <Grid fluid>
          {this.renderErrorMessage()}
          <Form horizontal onSubmit={this.createScan}>
            <Form.FormGroup controlId="scanName">
              <Grid.Col componentClass={Form.ControlLabel} sm={3}>
                <label htmlFor="scanName" className="control-label">
                  Name
                </label>
              </Grid.Col>
              <Grid.Col sm={9}>
                <Form.FormControl
                  type="text"
                  name="scanName"
                  autoFocus
                  value={scanName}
                  placeholder="Enter a name for the scan"
                  onChange={e => this.updateScanName(e)}
                  onKeyPress={e => this.onScanNameKeyPress(e)}
                />
              </Grid.Col>
            </Form.FormGroup>
            <Form.FormGroup>
              <Grid.Col componentClass={Form.ControlLabel} sm={3}>
                Sources
              </Grid.Col>
              <Grid.Col sm={9}>
                <Form.FormControl
                  className="quipucords-form-control"
                  componentClass="textarea"
                  type="textarea"
                  readOnly
                  rows={sources.length}
                  value={sources.map(item => item.name).join('\n')}
                />
              </Grid.Col>
            </Form.FormGroup>
          </Form>
        </Grid>
        <Modal.Footer>
          <Button bsStyle="default" className="btn-cancel" onClick={onClose}>
            Cancel
          </Button>
          <Button bsStyle="primary" type="submit" onClick={this.createScan} disabled={!validScanName}>
            Scan
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

CreateScanDialog.propTypes = {
  addScan: PropTypes.func,
  show: PropTypes.bool.isRequired,
  sources: PropTypes.array,
  onClose: PropTypes.func,
  action: PropTypes.object
};

export { CreateScanDialog };

const mapDispatchToProps = (dispatch, ownProps) => ({
  addScan: data => dispatch(addScan(data))
});

const mapStateToProps = function(state) {
  return Object.assign({}, { action: state.scans.action });
};

export default connect(mapStateToProps, mapDispatchToProps)(CreateScanDialog);
