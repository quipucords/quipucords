import React from 'react';
import PropTypes from 'prop-types';
import cx from 'classnames';
import { connect } from 'react-redux';
import { Button, Checkbox, Grid, Icon, ListView, OverlayTrigger, Popover } from 'patternfly-react';
import _ from 'lodash';
import * as moment from 'moment';
import { helpers } from '../../common/helpers';
import Store from '../../redux/store';
import { viewTypes } from '../../redux/constants';
import SourceCredentialsList from './sourceCredentialsList';
import ScanHostList from '../scanHostList/scanHostList';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';
import ListStatusItem from '../listStatusItem/listStatusItem';

class SourceListItem extends React.Component {
  static isSelected(item, selectedSources) {
    return _.find(selectedSources, nextSelected => nextSelected.id === item.id) !== undefined;
  }

  componentWillReceiveProps(nextProps) {
    const { lastRefresh } = this.props;
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, lastRefresh)) {
      this.closeExpandIfNoData(this.expandType());
    }
  }

  onItemSelectChange = () => {
    const { item, selectedSources } = this.props;

    Store.dispatch({
      type: SourceListItem.isSelected(item, selectedSources) ? viewTypes.DESELECT_ITEM : viewTypes.SELECT_ITEM,
      viewType: viewTypes.SOURCES_VIEW,
      item
    });
  };

  onToggleExpand = expandType => {
    const { item } = this.props;

    if (expandType === this.expandType()) {
      Store.dispatch({
        type: viewTypes.EXPAND_ITEM,
        viewType: viewTypes.SOURCES_VIEW,
        item
      });
    } else {
      Store.dispatch({
        type: viewTypes.EXPAND_ITEM,
        viewType: viewTypes.SOURCES_VIEW,
        item,
        expandType
      });
    }
  };

  onCloseExpand = () => {
    const { item } = this.props;
    Store.dispatch({
      type: viewTypes.EXPAND_ITEM,
      viewType: viewTypes.SOURCES_VIEW,
      item
    });
  };

  expandType() {
    const { item, expandedSources } = this.props;

    return _.get(_.find(expandedSources, nextExpanded => nextExpanded.id === item.id), 'expandType');
  }

  closeExpandIfNoData(expandType) {
    const { item } = this.props;

    if (expandType === 'okHosts' || expandType === 'failedHosts') {
      const okHostCount = _.get(item, 'connection.source_systems_scanned', 0);
      const failedHostCount = _.get(item, 'connection.source_systems_failed', 0);

      if ((expandType === 'okHosts' && okHostCount === 0) || (expandType === 'failedHosts' && failedHostCount === 0)) {
        this.onCloseExpand();
      }
    }
  }

  renderSourceType() {
    const { item } = this.props;
    const typeIcon = helpers.sourceTypeIcon(item.source_type);

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
            <Icon type="pf" name="edit" aria-label="Edit" />
          </Button>
        </SimpleTooltip>
        <SimpleTooltip id="deleteTip" tooltip="Delete">
          <Button onClick={() => onDelete(item)} bsStyle="link" key="removeButton">
            <Icon type="pf" name="delete" aria-label="Delete" />
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

    const expandType = this.expandType();
    const credentialCount = _.size(_.get(item, 'credentials', []));
    let okHostCount = _.get(item, 'connection.source_systems_scanned', 0);
    let failedHostCount = _.get(item, 'connection.source_systems_failed', 0);
    const unreachableHostCount = _.get(item, 'connection.source_systems_unreachable', 0);

    if (helpers.DEV_MODE) {
      okHostCount = helpers.devModeNormalizeCount(okHostCount);
      failedHostCount = helpers.devModeNormalizeCount(failedHostCount);
    }

    return [
      <ListStatusItem
        key="credential"
        id="credential"
        count={credentialCount}
        emptyText="0 Credentials"
        tipSingular="Credential"
        tipPlural="Credentials"
        expanded={expandType === 'credentials'}
        expandType="credentials"
        toggleExpand={this.onToggleExpand}
        iconInfo={{ type: 'fa', name: 'id-card' }}
      />,
      <ListStatusItem
        key="okHosts"
        id="okHosts"
        count={okHostCount}
        emptyText="0 Successful"
        tipSingular="Successful Authentication"
        tipPlural="Successful Authentications"
        expanded={expandType === 'okHosts'}
        expandType="okHosts"
        toggleExpand={this.onToggleExpand}
        iconInfo={helpers.scanStatusIcon('success')}
      />,
      <ListStatusItem
        key="failedHosts"
        id="failedHosts"
        count={failedHostCount}
        emptyText="0 Failed"
        tipSingular="Failed Authentication"
        tipPlural="Failed Authentications"
        expanded={expandType === 'failedHosts'}
        expandType="failedHosts"
        toggleExpand={this.onToggleExpand}
        iconInfo={helpers.scanStatusIcon('failed')}
      />,
      <ListStatusItem
        key="unreachableHosts"
        id="unreachableHosts"
        count={unreachableHostCount}
        emptyText="0 Unreachable"
        tipSingular="Unreachable System"
        tipPlural="Unreachable Systems"
        expanded={expandType === 'unreachableHosts'}
        expandType="unreachableHosts"
        toggleExpand={this.onToggleExpand}
        iconInfo={helpers.scanStatusIcon('unreachable')}
      />
    ];
  }

  static renderHostRow(host) {
    const iconInfo = helpers.scanStatusIcon(host.status);
    const classes = cx(...iconInfo.classNames);

    return (
      <React.Fragment>
        <Grid.Col xs={host.status === 'success' ? 6 : 12} sm={4}>
          <span>
            <Icon type={iconInfo.type} name={iconInfo.name} className={classes} />
            &nbsp; {host.name}
          </span>
        </Grid.Col>
        {host.status === 'success' && (
          <Grid.Col xs={6} sm={4}>
            <span>
              <Icon type="fa" name="id-card" />
              &nbsp; {host.credential.name}
            </span>
          </Grid.Col>
        )}
      </React.Fragment>
    );
  }

  renderExpansionContents() {
    const { item, lastRefresh } = this.props;

    switch (this.expandType()) {
      case 'okHosts':
        return (
          <ScanHostList
            scanId={item.connection.id}
            sourceId={item.id}
            lastRefresh={lastRefresh}
            status="success"
            renderHostRow={SourceListItem.renderHostRow}
            useConnectionResults
          />
        );
      case 'failedHosts':
        return (
          <ScanHostList
            scanId={item.connection.id}
            sourceId={item.id}
            lastRefresh={lastRefresh}
            status="failed"
            renderHostRow={SourceListItem.renderHostRow}
            useConnectionResults
          />
        );
      case 'unreachableHosts':
        return (
          <ScanHostList
            scanId={item.connection.id}
            sourceId={item.id}
            lastRefresh={lastRefresh}
            status="unreachable"
            renderHostRow={SourceListItem.renderHostRow}
            useConnectionResults
          />
        );
      case 'credentials':
        return <SourceCredentialsList source={item} />;
      default:
        return null;
    }
  }

  renderDescription() {
    const { item } = this.props;

    const itemHostsPopover = (
      <Popover id={helpers.generateId()} className="quipucords-sources-popover-scroll">
        {item.hosts &&
          item.hosts.length > 1 && (
            <ul className="quipucords-popover-list">
              {item.hosts.map(host => (
                <li>{host}</li>
              ))}
            </ul>
          )}
        {item.hosts && item.hosts.length === 1 && <div>{item.hosts[0]}</div>}
      </Popover>
    );

    let itemDescription;

    if (_.size(item.hosts)) {
      if (item.source_type === 'network') {
        itemDescription = (
          <ListView.DescriptionText>
            <OverlayTrigger trigger="click" rootClose placement="left" overlay={itemHostsPopover}>
              <Button bsStyle="link" className="quipucords-sources-network-button">
                Network Range
              </Button>
            </OverlayTrigger>
          </ListView.DescriptionText>
        );
      } else {
        itemDescription = <ListView.DescriptionText>{item.hosts[0]}</ListView.DescriptionText>;
      }
    }

    return (
      <div className="quipucords-split-description">
        <span className="quipucords-description-left">
          <ListView.DescriptionHeading>{item.name}</ListView.DescriptionHeading>
          {itemDescription}
        </span>
        <span className="quipucords-description-right">{this.renderScanStatus()}</span>
      </div>
    );
  }

  renderScanStatus() {
    const { item } = this.props;

    const scan = _.get(item, 'connection');
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
    const { item, selectedSources } = this.props;
    const selected = SourceListItem.isSelected(item, selectedSources);

    const classes = cx({
      'list-view-pf-top-align': true,
      active: selected
    });

    return (
      <ListView.Item
        key={item.id}
        stacked
        className={classes}
        checkboxInput={<Checkbox checked={selected} bsClass="" onChange={this.onItemSelectChange} />}
        actions={this.renderActions()}
        leftContent={this.renderSourceType()}
        description={this.renderDescription()}
        additionalInfo={this.renderStatusItems()}
        compoundExpand
        compoundExpanded={this.expandType() !== undefined}
        onCloseCompoundExpand={this.onCloseExpand}
      >
        {this.renderExpansionContents()}
      </ListView.Item>
    );
  }
}

SourceListItem.propTypes = {
  item: PropTypes.object.isRequired,
  lastRefresh: PropTypes.number,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
  onScan: PropTypes.func,
  selectedSources: PropTypes.array,
  expandedSources: PropTypes.array
};

SourceListItem.defaultProps = {
  lastRefresh: 0,
  onEdit: helpers.noop,
  onDelete: helpers.noop,
  onScan: helpers.noop,
  selectedSources: [],
  expandedSources: []
};

const mapStateToProps = state =>
  Object.assign({
    selectedSources: state.viewOptions[viewTypes.SOURCES_VIEW].selectedItems,
    expandedSources: state.viewOptions[viewTypes.SOURCES_VIEW].expandedItems
  });

const ConnectedSourceListItem = connect(mapStateToProps)(SourceListItem);

export { ConnectedSourceListItem as default, ConnectedSourceListItem, SourceListItem };
