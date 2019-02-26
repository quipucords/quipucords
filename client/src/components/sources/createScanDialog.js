import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Alert, Modal, Button, Form, Grid, Icon } from 'patternfly-react';
import helpers from '../../common/helpers';
import Store from '../../redux/store';
import { reduxActions } from '../../redux/actions';
import { scansTypes, toastNotificationTypes } from '../../redux/constants';

class CreateScanDialog extends React.Component {
  static validateScanName(scanName) {
    return scanName && scanName.length > 0;
  }

  constructor() {
    super();

    this.state = {
      scanName: '',
      validScanName: false
    };
  }

  componentWillReceiveProps(nextProps) {
    const { show } = this.props;

    if (nextProps.show && !show) {
      this.setState({ scanName: '', validScanName: false });
      Store.dispatch({
        type: scansTypes.RESET_SCAN_ADD_STATUS
      });
    }
  }

  onCreateScan = () => {
    const { sources, addScan } = this.props;
    const { scanName } = this.state;

    const data = {
      name: scanName,
      sources: sources.map(item => item.id)
    };

    addScan(data).then(
      response => this.notifyAddStatus(false, response.value),
      error => this.notifyAddStatus(true, error)
    );
  };

  onUpdateScanName = event => {
    this.setState({
      scanName: event.target.value,
      validScanName: CreateScanDialog.validateScanName(event.target.value)
    });
  };

  onScanNameKeyPress = keyEvent => {
    const { scanName, validScanName } = this.state;

    if (keyEvent.key === 'Enter' && scanName && validScanName) {
      keyEvent.stopPropagation();
      keyEvent.preventDefault();
      this.onCreateScan();
    }
  };

  onErrorDismissed = () => {
    Store.dispatch({
      type: scansTypes.RESET_SCAN_ADD_STATUS
    });
  };

  notifyStartStatus(error, results) {
    const { onClose } = this.props;
    const { scanName } = this.state;

    if (error) {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'error',
        header: 'Error',
        message: helpers.getMessageFromResults(results).message
      });
    } else {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'success',
        message: (
          <span>
            Started scan <strong>{scanName}</strong>.
          </span>
        )
      });
    }
    onClose(true);
  }

  startNewScan(newScan) {
    const { startScan } = this.props;

    startScan(newScan.id).then(
      response => this.notifyStartStatus(false, response.value),
      error => this.notifyStartStatus(true, error)
    );
  }

  notifyAddStatus(error, results) {
    const { scanName } = this.state;

    if (error) {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'error',
        header: 'Error',
        message: helpers.getMessageFromResults(results).message
      });
    } else {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'success',
        message: (
          <span>
            Added scan <strong>{scanName}</strong>.
          </span>
        )
      });

      this.startNewScan(results.data);
    }
  }

  renderErrorMessage() {
    const { action } = this.props;

    if (action && action.error) {
      return (
        <Alert type="error" onDismiss={this.onErrorDismissed}>
          <strong>Error</strong> {action.errorMessage}
        </Alert>
      );
    }

    return null;
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
          <button type="button" className="close" onClick={onClose} aria-hidden="true" aria-label="Close">
            <Icon type="pf" name="close" />
          </button>
          <Modal.Title>Scan</Modal.Title>
        </Modal.Header>
        <Modal.Body />
        <Grid fluid>
          {this.renderErrorMessage()}
          <Form horizontal onSubmit={this.onCreateScan}>
            <Form.FormGroup controlId="scanName">
              <Grid.Col componentClass={Form.ControlLabel} sm={3}>
                Name
              </Grid.Col>
              <Grid.Col sm={9}>
                <Form.FormControl
                  type="text"
                  name="scanName"
                  autoFocus
                  value={scanName}
                  placeholder="Enter a name for the scan"
                  onChange={e => this.onUpdateScanName(e)}
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
          <Button bsStyle="primary" type="submit" onClick={this.onCreateScan} disabled={!validScanName}>
            Scan
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

CreateScanDialog.propTypes = {
  addScan: PropTypes.func,
  startScan: PropTypes.func,
  show: PropTypes.bool.isRequired,
  sources: PropTypes.array,
  onClose: PropTypes.func,
  action: PropTypes.object
};

CreateScanDialog.defaultProps = {
  addScan: helpers.noop,
  startScan: helpers.noop,
  sources: [],
  onClose: helpers.noop,
  action: {}
};

const mapDispatchToProps = dispatch => ({
  addScan: data => dispatch(reduxActions.scans.addScan(data)),
  startScan: data => dispatch(reduxActions.scans.startScan(data))
});

const mapStateToProps = state => ({ action: state.scans.action });

const ConnectedCreateScanDialog = connect(
  mapStateToProps,
  mapDispatchToProps
)(CreateScanDialog);

export { ConnectedCreateScanDialog as default, ConnectedCreateScanDialog, CreateScanDialog };
