import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { AboutModal } from 'patternfly-react';

import Store from '../../redux/store';

import { aboutTypes } from '../../redux/constants';
import logo from '../../styles/images/Red_Hat_logo.svg';
import productTitle from '../../styles/images/title.svg';

class About extends React.Component {

  closeAbout() {
    Store.dispatch({ type: aboutTypes.ABOUT_DIALOG_CLOSE });
  }

  render() {
    const { showAbout } = this.props;

    return (
      <AboutModal
        key="aboutModal"
        show={showAbout}
        onHide={this.closeAbout}
        productTitle={
          <img src={productTitle} alt="Red Hat Entitlements Reporting"/>
        }
        logo={logo}
        altLogo="RH ER"
        trademarkText="Copyright (c) 2018 Red Hat Inc."
      >
        <AboutModal.Versions>
          <AboutModal.VersionItem label="Label" versionText="Version"/>
          <AboutModal.VersionItem label="Label" versionText="Version"/>
          <AboutModal.VersionItem label="Label" versionText="Version"/>
          <AboutModal.VersionItem label="Label" versionText="Version"/>
          <AboutModal.VersionItem label="Label" versionText="Version"/>
          <AboutModal.VersionItem label="Label" versionText="Version"/>
          <AboutModal.VersionItem label="Label" versionText="Version"/>
        </AboutModal.Versions>
      </AboutModal>
    );
  }
}

About.propTypes = {
  showAbout: PropTypes.bool
}

function mapStateToProps(state, ownProps) {
  return {
    showAbout: state.about.show
  };
};

export default connect(mapStateToProps)(About);
