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
      confirmIcon,
      confirmButtonText,
      cancelButtonText,
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
          <div className="confirm-modal-body">
            {confirmIcon && (
              <span className="confirm-modal-icon">{confirmIcon}</span>
            )}
            <span className="confirm-modal-content">
              <span className="spacer" />
              <p>{confirmHeading}</p>
              <p>{confirmBody}</p>
              <span className="spacer" />
            </span>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button
            autoFocus
            bsStyle="default"
            className="btn-cancel"
            onClick={this.cancel}
          >
            {cancelButtonText}
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
  confirmHeading: PropTypes.node,
  confirmIcon: PropTypes.node,
  confirmBody: PropTypes.node,
  confirmButtonText: PropTypes.string,
  cancelButtonText: PropTypes.string,
  onConfirm: PropTypes.func,
  onCancel: PropTypes.func
};
ConfirmationModal.defaultProps = {
  confirmTitle: 'Confirm',
  confirmHeading: null,
  confirmBody: null,
  confirmIcon: <Icon type="pf" name="warning-triangle-o" />,
  confirmButtonText: 'Confirm'
};

function mapStateToProps(state, ownProps) {
  return {
    show: state.confirmationModal.show,
    confirmTitle: state.confirmationModal.title,
    confirmHeading: state.confirmationModal.heading,
    confirmIcon: state.confirmationModal.icon,
    confirmBody: state.confirmationModal.body,
    confirmButtonText: state.confirmationModal.confirmButtonText,
    cancelButtonText: state.confirmationModal.cancelButtonText,
    onConfirm: state.confirmationModal.onConfirm,
    onCancel: state.confirmationModal.onCancel
  };
}

export default connect(mapStateToProps)(ConfirmationModal);
