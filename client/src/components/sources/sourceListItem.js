import _ from 'lodash';
import * as moment from 'moment';
import React from 'react';
import { connect } from 'react-redux';
import cx from 'classnames';
import PropTypes from 'prop-types';

import { ListView, Button, Checkbox, Icon } from 'patternfly-react';

import { helpers } from '../../common/helpers';
import { getScanResults } from '../../redux/actions/scansActions';

import { SourceCredentialsList } from './sourceCredentialsList';
import SourceHostList from './sourceHostList';
import { SimpleTooltip } from '../simpleTooltIp/simpleTooltip';

class SourceListItem extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['toggleExpand', 'closeExpand']);
  }

  toggleExpand(expandType) {
    const { item } = this.props;

    if (expandType === item.expandType) {
      item.expanded = !item.expanded;
    } else {
      item.expanded = true;
      item.expandType = expandType;

      if (expandType === 'okHosts' || expandType === 'failedHosts') {
        if (!item.scanResults) {
          item.scanResultsPending = true;
          item.scanResultsError = null;
          this.props
            .getScanResults(item.connection.id)
            .then(results => {
              console.dir(results);
              item.scanResultsPending = false;
              item.scanResults = _.get(results.value, 'data');
            })
            .catch(error => {
              item.scanResultsPending = false;
              item.scanResultsError = _.get(error.payload, 'response.request.responseText', error.payload.message);
            })
            .finally(() => {
              item.scanResultsPending = false;
              this.forceUpdate();
            });
        }
      }
    }
    this.forceUpdate();
  }

  closeExpand() {
    const { item } = this.props;
    item.expanded = false;
    this.forceUpdate();
  }

  renderSourceType() {
    const { item } = this.props;

    let typeIcon = helpers.sourceTypeIcon(item.source_type);

    return (
      <SimpleTooltip id="sourceTypeTip" tooltip={helpers.sourceTypeString(item.source_type)}>
        <ListView.Icon type={typeIcon.type} name={typeIcon.name} />
      </SimpleTooltip>
    );
  }

  renderActions() {
    const { item, onEdit, onDelete, onScan } = this.props;

    return (
      <span>
        <SimpleTooltip id="editTip" tooltip="Edit">
          <Button onClick={() => onEdit(item)} bsStyle="link" key="editButton">
            <Icon type="pf" name="edit" atria-label="Edit" />
          </Button>
        </SimpleTooltip>
        <SimpleTooltip id="deleteTip" tooltip="Delete">
          <Button onClick={() => onDelete(item)} bsStyle="link" key="removeButton">
            <Icon type="pf" name="delete" atria-label="Delete" />
          </Button>
        </SimpleTooltip>
        <Button onClick={() => onScan(item)} key="scanButton">
          Scan
        </Button>
      </span>
    );
  }

  renderStatusItems() {
    const { item } = this.props;

    let credentialCount = _.size(_.get(item, 'credentials', []));
    let okHostCount = _.get(item, 'connection.systems_scanned', 0);
    let failedHostCount = _.get(item, 'connection.systems_failed', 0);

    if (helpers.DEV_MODE) {
      okHostCount = helpers.normalizeCount(okHostCount);
      failedHostCount = helpers.normalizeCount(failedHostCount);
    }

    return [
      <ListView.InfoItem
        key="credentials"
        className={'list-view-info-item-icon-count ' + (credentialCount === 0 ? 'invisible' : '')}
      >
        <SimpleTooltip
          id="credentialsTip"
          tooltip={credentialCount + (credentialCount === 1 ? ' Credential' : ' Credentials')}
        >
          <ListView.Expand
            expanded={item.expanded && item.expandType === 'credentials'}
            toggleExpanded={() => {
              this.toggleExpand('credentials');
            }}
          >
            <Icon className="list-view-compound-item-icon" type="fa" name="id-card" />
            <strong>{credentialCount}</strong>
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>,
      <ListView.InfoItem
        key="okHosts"
        className={'list-view-info-item-icon-count ' + (okHostCount === 0 ? 'invisible' : '')}
      >
        <SimpleTooltip
          id="okHostsTip"
          tooltip={okHostCount + (okHostCount === 1 ? ' Successful Authentication' : ' Successful Authentications')}
        >
          <ListView.Expand
            expanded={item.expanded && item.expandType === 'okHosts'}
            toggleExpanded={() => {
              this.toggleExpand('okHosts');
            }}
          >
            <Icon className="list-view-compound-item-icon" type="pf" name="ok" />
            <strong>{okHostCount}</strong>
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>,
      <ListView.InfoItem
        key="failedHosts"
        className={'list-view-info-item-icon-count ' + (failedHostCount === 0 ? 'invisible' : '')}
      >
        <SimpleTooltip
          id="failedHostsTip"
          tooltip={failedHostCount + (failedHostCount === 1 ? ' Failed Authentication' : ' Failed Authentications')}
        >
          <ListView.Expand
            expanded={item.expanded && item.expandType === 'failedHosts'}
            toggleExpanded={() => {
              this.toggleExpand('failedHosts');
            }}
          >
            <Icon className="list-view-compound-item-icon" type="pf" name="error-circle-o" />
            <strong>{failedHostCount}</strong>
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>
    ];
  }

  renderExpansionContents() {
    const { item } = this.props;

    switch (item.expandType) {
      case 'okHosts':
        return <SourceHostList source={item} status="success" />;
      case 'failedHosts':
        return <SourceHostList source={item} status="failed" />;
      case 'credentials':
        return <SourceCredentialsList source={item} />;
      default:
        return null;
    }
  }

  renderDescription() {
    const { item } = this.props;
    return (
      <div className="quipucords-split-description">
        <span className="quipucords-description-left">
          <ListView.DescriptionHeading>{item.name}</ListView.DescriptionHeading>
          {item.hosts &&
            item.hosts.map((host, index) => {
              return <ListView.DescriptionText key={index}>{host}</ListView.DescriptionText>;
            })}
        </span>
        <span className="quipucords-description-right">{this.renderScanStatus()}</span>
      </div>
    );
  }

  renderScanStatus() {
    const { item } = this.props;

    let scan = _.get(item, 'connection');
    let scanDescription = '';
    let scanTime = _.get(scan, 'end_time');

    let icon = null;
    switch (_.get(scan, 'status')) {
      case 'completed':
        scanDescription = 'Last Connected';
        icon = <Icon className="scan-status-icon" type="pf" name="ok" />;
        break;
      case 'failed':
        scanDescription = 'Connection Failed';
        icon = <Icon className="scan-status-icon" type="pf" name="error-circle-o" />;
        break;
      case 'canceled':
        scanDescription = 'Connection Canceled';
        icon = <Icon className="scan-status-icon" type="pf" name="error-circle-o" />;
        break;
      case 'created':
      case 'pending':
      case 'running':
        scanTime = _.get(scan, 'start_time');
        scanDescription = 'Connection in Progress';
        icon = <Icon className="scan-status-icon fa-spin" type="fa" name="spinner" />;
        break;
      case 'paused':
        scanDescription = 'Connection Paused';
        icon = <Icon className="scan-status-icon" type="pf" name="warning-triangle-o" />;
        break;
      default:
        return null;
    }

    return (
      <div className="scan-description">
        {icon}
        <div className="scan-status-text">
          <div>{scanDescription}</div>
          <div>
            {moment
              .utc(scanTime)
              .utcOffset(moment().utcOffset())
              .fromNow()}
          </div>
        </div>
      </div>
    );
  }
  render() {
    const { item, selected, onItemSelectChange } = this.props;

    const classes = cx({
      'list-view-pf-top-align': true,
      active: selected
    });

    return (
      <ListView.Item
        key={item.id}
        stacked
        className={classes}
        checkboxInput={<Checkbox checked={selected} bsClass="" onClick={e => onItemSelectChange(item)} />}
        actions={this.renderActions()}
        leftContent={this.renderSourceType()}
        description={this.renderDescription()}
        additionalInfo={this.renderStatusItems()}
        compoundExpand
        compoundExpanded={item.expanded}
        onCloseCompoundExpand={this.closeExpand}
      >
        {this.renderExpansionContents()}
      </ListView.Item>
    );
  }
}

SourceListItem.propTypes = {
  item: PropTypes.object,
  selected: PropTypes.bool,
  onItemSelectChange: PropTypes.func,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
  onScan: PropTypes.func,
  getScanResults: PropTypes.func
};

const mapStateToProps = function(state) {
  return {};
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScanResults: id => dispatch(getScanResults(id))
});

export default connect(mapStateToProps, mapDispatchToProps)(SourceListItem);
