import React from 'react';
import PropTypes from 'prop-types';
import { Button, Icon } from 'patternfly-react';
import * as moment from 'moment';
import helpers from '../../common/helpers';

class RefreshTimeButton extends React.Component {
  constructor(props) {
    super(props);

    helpers.bindMethods(this, ['doUpdate']);

    this.pollingInterval = null;
    this.mounted = false;
  }

  componentDidMount() {
    this.mounted = true;
  }

  componentWillUnmount() {
    this.stopPolling();
    this.mounted = false;
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.lastRefresh && !this.lastRefresh) {
      this.startPolling();
    }
  }

  doUpdate() {
    this.forceUpdate();
  }

  startPolling() {
    if (!this.pollingInterval && this.mounted) {
      this.pollingInterval = setInterval(this.doUpdate, 3000);
    }
  }

  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  render() {
    const { lastRefresh, onRefresh } = this.props;

    return (
      <Button onClick={onRefresh} bsStyle="link" className="refresh-button">
        <Icon type="fa" name="refresh" />
        <span className="last-refresh-time">
          Refreshed{' '}
          {lastRefresh &&
            moment
              .utc(lastRefresh)
              .utcOffset(moment().utcOffset())
              .fromNow()}
        </span>
      </Button>
    );
  }
}

RefreshTimeButton.propTypes = {
  lastRefresh: PropTypes.number,
  onRefresh: PropTypes.func.isRequired
};

export { RefreshTimeButton as default, RefreshTimeButton };
