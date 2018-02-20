import React from 'react';
import PropTypes from 'prop-types';

import { Modal, Button, Form, Grid, Icon } from 'patternfly-react';

import helpers from '../../common/helpers';

class CreateScanDialog extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['updateScanName', 'confirm']);
    this.state = {
      scanName: '',
      validScanName: false
    };
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.show && !this.props.show) {
      this.setState({ scanName: '', validScanName: false });
    }
  }

  nameExists(name) {
    const { scans } = this.props;
    return (
      scans &&
      scans.find(scan => {
        return scan.name === name;
      })
    );
  }

  validateScanName(scanName) {
    return scanName && scanName.length > 0 && !this.nameExists(scanName);
  }

  updateScanName(event) {
    this.setState({
      scanName: event.target.value,
      validScanName: this.validateScanName(event.target.value)
    });
  }

  confirm() {
    const { sources, onScan } = this.props;
    const { scanName } = this.state;

    onScan(scanName, sources);
  }

  render() {
    const { show, sources, onCancel } = this.props;
    const { scanName, validScanName } = this.state;

    if (!sources || sources.length === 0 || !sources[0]) {
      return null;
    }

    return (
      <Modal show={show} onHide={onCancel}>
        <Modal.Header>
          <button className="close" onClick={onCancel} aria-hidden="true" aria-label="Close">
            <Icon type="pf" name="close" />
          </button>
          <Modal.Title>Scan</Modal.Title>
        </Modal.Header>
        <Modal.Body />
        <Grid fluid>
          <Form horizontal>
            <Form.FormGroup>
              <Grid.Col componentClass={Form.ControlLabel} sm={3}>
                Name
              </Grid.Col>
              <Grid.Col sm={9}>
                <Form.FormControl type="text" autoFocus value={scanName} onChange={e => this.updateScanName(e)} />
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
          <Button bsStyle="default" className="btn-cancel" onClick={onCancel}>
            Cancel
          </Button>
          <Button bsStyle="primary" onClick={this.confirm} disabled={!validScanName}>
            Scan
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

CreateScanDialog.propTypes = {
  show: PropTypes.bool.isRequired,
  sources: PropTypes.array,
  scans: PropTypes.object,
  onScan: PropTypes.func,
  onCancel: PropTypes.func
};

export { CreateScanDialog };
