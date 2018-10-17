import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Modal, Button, Icon } from 'patternfly-react';
import Store from '../../redux/store';
import { confirmationModalTypes } from '../../redux/constants';
import helpers from '../../common/helpers';

class ConfirmationModal extends React.Component {
  onClose = () => {
    const { onCancel } = this.props;

    if (onCancel) {
      onCancel();
    } else {
      Store.dispatch({
        type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
      });
    }
  };

  render() {
    const { show, title, heading, body, icon, confirmButtonText, cancelButtonText, onConfirm } = this.props;

    return (
      <Modal show={show} onHide={this.onClose}>
        <Modal.Header>
          <button type="button" className="close" onClick={this.onClose} aria-hidden="true" aria-label="Close">
            <Icon type="pf" name="close" />
          </button>
          <Modal.Title>{title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="confirm-modal-body">
            {icon && <span className="confirm-modal-icon">{icon}</span>}
            <span className="confirm-modal-content">
              <span className="spacer" />
              <div className="confirm-modal-content-heading">{heading}</div>
              <div>{body}</div>
              <span className="spacer" />
            </span>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button autoFocus bsStyle="default" className="btn-cancel" onClick={this.onClose}>
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
  title: PropTypes.string,
  heading: PropTypes.node,
  icon: PropTypes.node,
  body: PropTypes.node,
  confirmButtonText: PropTypes.string,
  cancelButtonText: PropTypes.string,
  onConfirm: PropTypes.func,
  onCancel: PropTypes.func
};

ConfirmationModal.defaultProps = {
  title: 'Confirm',
  heading: null,
  body: null,
  icon: <Icon type="pf" name="warning-triangle-o" />,
  confirmButtonText: 'Confirm',
  cancelButtonText: '',
  onConfirm: helpers.noop,
  onCancel: null
};

const mapStateToProps = state => ({ ...state.confirmationModal });

const ConnectedConfirmationModal = connect(mapStateToProps)(ConfirmationModal);

export { ConnectedConfirmationModal as default, ConnectedConfirmationModal, ConfirmationModal };
