import { connect } from 'react-redux';
import React from 'react';
import PropTypes from 'prop-types';

import { Modal, Button, Icon } from 'patternfly-react';

import { bindMethods } from '../../common/helpers';
import Store from '../../redux/store';
import { confirmationModalTypes } from '../../redux/constants';

class ConfirmationModal extends React.Component {
  constructor() {
    super();

    bindMethods(this, ['cancel']);
  }

  cancel() {
    if (this.props.onCancel) {
      this.props.onCancel();
    } else {
      Store.dispatch({
        type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
      });
    }
  }

  render() {
    const {
      show,
      confirmTitle,
      confirmHeading,
      confirmBody,
      confirmButtonText,
      onConfirm
    } = this.props;

    return (
      <Modal show={show} onHide={this.cancel}>
        <Modal.Header>
          <button
            className="close"
            onClick={this.cancel}
            aria-hidden="true"
            aria-label="Close"
          >
            <Icon type="pf" name="close" />
          </button>
          <Modal.Title>{confirmTitle}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {confirmHeading}
          <p>{confirmBody}</p>
        </Modal.Body>
        <Modal.Footer>
          <Button
            bsStyle="default"
            className="btn-cancel"
            onClick={this.cancel}
          >
            Cancel
          </Button>
          <Button bsStyle="primary" onClick={onConfirm}>
            {confirmButtonText}
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

ConfirmationModal.propTypes = {
  show: PropTypes.bool.isRequired,
  confirmTitle: PropTypes.string,
  confirmHeading: PropTypes.object,
  confirmBody: PropTypes.object,
  confirmButtonText: PropTypes.string,
  onConfirm: PropTypes.func,
  onCancel: PropTypes.func
};
ConfirmationModal.defaultProps = {
  confirmTitle: 'Confirm',
  confirmHeading: null,
  confirmBody: null,
  confirmButtonText: 'Confirm'
};

function mapStateToProps(state, ownProps) {
  return {
    show: state.confirmationModal.show,
    confirmTitle: state.confirmationModal.title,
    confirmHeading: state.confirmationModal.heading,
    confirmBody: state.confirmationModal.body,
    confirmButtonText: state.confirmationModal.confirmButtonText,
    onConfirm: state.confirmationModal.onConfirm,
    onCancel: state.confirmationModal.onCancel
  };
}

export default connect(mapStateToProps)(ConfirmationModal);
