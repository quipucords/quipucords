import { connect } from 'react-redux';
import React from 'react';
import PropTypes from 'prop-types';

import {
  ToastNotificationList,
  TimedToastNotification
} from 'patternfly-react';

import helpers from '../../common/helpers';
import Store from '../../redux/store';
import { toastNotificationTypes } from '../../redux/constants';

class ToastNotificationsList extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['onHover', 'onLeave', 'onDismiss']);
  }

  onHover() {
    Store.dispatch({ type: toastNotificationTypes.TOAST_PAUSE });
  }

  onLeave() {
    Store.dispatch({ type: toastNotificationTypes.TOAST_RESUME });
  }

  onDismiss(toast) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_REMOVE,
      toast: toast
    });
  }

  render() {
    const { toasts, paused } = this.props;

    return (
      <ToastNotificationList>
        {toasts &&
          toasts.map((toast, index) => {
            if (!toast.removed) {
              return (
                <TimedToastNotification
                  key={index}
                  toastIndex={index}
                  type={toast.alertType}
                  paused={paused}
                  onDismiss={e => this.onDismiss(toast)}
                  onMouseEnter={this.onHover}
                  onMouseLeave={this.onLeave}
                >
                  <span>
                    <strong>{toast.header}</strong> &nbsp;
                    {toast.message}
                  </span>
                </TimedToastNotification>
              );
            } else {
              return null;
            }
          })}
      </ToastNotificationList>
    );
  }
}

ToastNotificationsList.propTypes = {
  toasts: PropTypes.array,
  paused: PropTypes.bool
};

function mapStateToProps(state, ownProps) {
  return {
    toasts: state.toastNotifications.toasts,
    paused: state.toastNotifications.paused
  };
}

export default connect(mapStateToProps)(ToastNotificationsList);
