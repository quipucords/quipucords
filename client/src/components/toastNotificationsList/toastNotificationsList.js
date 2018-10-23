import React from 'react';
import PropTypes from 'prop-types';
import { ToastNotificationList, TimedToastNotification } from 'patternfly-react';
import { connect } from 'react-redux';
import Store from '../../redux/store';
import { toastNotificationTypes } from '../../redux/constants';
import helpers from '../../common/helpers';

class ToastNotificationsList extends React.Component {
  onHover = () => {
    Store.dispatch({ type: toastNotificationTypes.TOAST_PAUSE });
  };

  onLeave = () => {
    Store.dispatch({ type: toastNotificationTypes.TOAST_RESUME });
  };

  onDismiss = toast => {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_REMOVE,
      toast
    });
  };

  render() {
    const { toasts, paused } = this.props;

    return (
      <ToastNotificationList>
        {toasts &&
          toasts.map((toast, index) => {
            if (!toast.removed) {
              return (
                <TimedToastNotification
                  key={helpers.generateId('key')}
                  toastIndex={index}
                  type={toast.alertType}
                  paused={paused}
                  onDismiss={() => this.onDismiss(toast)}
                  onMouseEnter={this.onHover}
                  onMouseLeave={this.onLeave}
                >
                  <span>
                    <strong>{toast.header}</strong> &nbsp;
                    {toast.message}
                  </span>
                </TimedToastNotification>
              );
            }

            return null;
          })}
      </ToastNotificationList>
    );
  }
}

ToastNotificationsList.propTypes = {
  toasts: PropTypes.array,
  paused: PropTypes.bool
};

ToastNotificationsList.defaultProps = {
  toasts: [],
  paused: false
};

const mapStateToProps = state => ({ ...state.toastNotifications });

const ConnectedToastNotificationsList = connect(mapStateToProps)(ToastNotificationsList);

export { ConnectedToastNotificationsList as default, ConnectedToastNotificationsList, ToastNotificationsList };
