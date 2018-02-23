import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import browser from 'detect-browser';

import { AboutModal } from 'patternfly-react';

import Store from '../../redux/store';

import { aboutTypes } from '../../redux/constants';
import logo from '../../styles/images/Red_Hat_logo.svg';
import productTitle from '../../styles/images/title.svg';
import { getUser } from '../../redux/actions/userActions';

class About extends React.Component {
  componentDidMount() {
    this.props.getUser();
  }

  closeAbout() {
    Store.dispatch({ type: aboutTypes.ABOUT_DIALOG_CLOSE });
  }

  render() {
    const { showAbout, user } = this.props;

    return (
      <AboutModal
        key="aboutModal"
        show={showAbout}
        onHide={this.closeAbout}
        productTitle={<img src={productTitle} alt="Red Hat Entitlements Reporting" />}
        logo={logo}
        altLogo="RH ER"
        trademarkText="Copyright (c) 2018 Red Hat Inc."
      >
        <AboutModal.Versions>
          <AboutModal.VersionItem label="Sonar Version" versionText="0.1" />
          <AboutModal.VersionItem label="Username" versionText={_.get(user, 'currentUser.username', '')} />
          <AboutModal.VersionItem
            label="Browser Version"
            versionText={`${_.get(browser, 'name', '')} ${_.get(browser, 'version', '')}`}
          />
          <AboutModal.VersionItem label="Browser OS" versionText={_.get(browser, 'os', '')} />
        </AboutModal.Versions>
      </AboutModal>
    );
  }
}

About.propTypes = {
  getUser: PropTypes.func,
  user: PropTypes.object,
  showAbout: PropTypes.bool
};

function mapStateToProps(state, ownProps) {
  return {
    showAbout: state.about.show,
    user: state.user.user
  };
}

const mapDispatchToProps = (dispatch, ownProps) => ({
  getUser: () => dispatch(getUser())
});

export default connect(mapStateToProps, mapDispatchToProps)(About);
